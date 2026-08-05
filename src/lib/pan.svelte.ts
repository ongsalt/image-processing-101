// pan-zoom.svelte.ts
import type { Attachment } from 'svelte/attachments';

export interface Transform {
  x: number;
  y: number;
  scale: number;
}

export interface PanZoomOptions {
  minScale?: number;
  maxScale?: number;
  /** Exponent factor for pinch/ctrl-wheel zoom. Higher = faster. */
  zoomSpeed?: number;
  /** Multiplier on touchpad pan deltas. GNOME/libinput runs hot; try 0.3–0.5. */
  panSpeed?: number;
  /** Multiplier on mouse-wheel pan deltas (sparse, large deltas). */
  wheelPanSpeed?: number;
  /** Pixels per line when deltaMode is LINE (Firefox). */
  lineHeight?: number;
  /** Initial transform. */
  initial?: Partial<Transform>;
  onChange?: (t: Transform) => void;
}

function defaultPanSpeed(): number {
  if (typeof navigator === 'undefined') return 1;
  const ua = navigator.userAgent;
  if (/Mac/.test(ua)) return 1;
  if (/Firefox/.test(ua)) return 0.6;
  if (/Linux/.test(ua)) return 0.4;
  return 1;
}

export class PanZoomState {
  x = $state(0);
  y = $state(0);
  scale = $state(1);

  #minScale: number;
  #maxScale: number;
  #zoomSpeed: number;
  #panSpeed: number;
  #wheelPanSpeed: number;
  #lineHeight: number;
  #onChange?: (t: Transform) => void;

  #rect: DOMRect | null = null;
  #dragId: number | null = null;
  #lastX = 0;
  #lastY = 0;

  constructor(opts: PanZoomOptions = {}) {
    this.#minScale = $state(opts.minScale ?? 0.1);
    this.#maxScale = $state(opts.maxScale ?? 32);
    this.#zoomSpeed = $state(opts.zoomSpeed ?? 0.01);
    this.#panSpeed = $state(opts.panSpeed ?? defaultPanSpeed());
    this.#wheelPanSpeed = $state(opts.wheelPanSpeed ?? 1);
    this.#lineHeight = $state(opts.lineHeight ?? 16);
    this.#onChange = $state(opts.onChange);

    this.x = opts.initial?.x ?? 0;
    this.y = opts.initial?.y ?? 0;
    this.scale = opts.initial?.scale ?? 1;
  }

  // --- tunables (live-adjustable, e.g. from a settings panel) ---------------

  get panSpeed() { return this.#panSpeed; }
  set panSpeed(v: number) { this.#panSpeed = v; }

  get wheelPanSpeed() { return this.#wheelPanSpeed; }
  set wheelPanSpeed(v: number) { this.#wheelPanSpeed = v; }

  get zoomSpeed() { return this.#zoomSpeed; }
  set zoomSpeed(v: number) { this.#zoomSpeed = v; }

  // --- reads ---------------------------------------------------------------

  get transform(): Transform {
    return { x: this.x, y: this.y, scale: this.scale };
  }

  get cssTransform(): string {
    return `translate(${this.x}px, ${this.y}px) scale(${this.scale})`;
  }

  /** Column-major 3x2 affine, for canvas/GPU consumers. */
  get matrix(): [number, number, number, number, number, number] {
    return [this.scale, 0, 0, this.scale, this.x, this.y];
  }

  /** Element-space point -> content-space point. */
  toContent(px: number, py: number) {
    return { x: (px - this.x) / this.scale, y: (py - this.y) / this.scale };
  }

  /** Content-space point -> element-space point. */
  toScreen(cx: number, cy: number) {
    return { x: cx * this.scale + this.x, y: cy * this.scale + this.y };
  }

  // --- mutations -----------------------------------------------------------

  set(t: Partial<Transform>) {
    if (t.x !== undefined) this.x = t.x;
    if (t.y !== undefined) this.y = t.y;
    if (t.scale !== undefined) {
      this.scale = Math.min(this.#maxScale, Math.max(this.#minScale, t.scale));
    }
    this.#notify();
  }

  reset() {
    this.set({ x: 0, y: 0, scale: 1 });
  }

  panBy(dx: number, dy: number) {
    this.x += dx;
    this.y += dy;
    this.#notify();
  }

  /**
   * Zoom about a point in element space. The content under that point stays
   * fixed, including when the result is partially clamped.
   */
  zoomAt(px: number, py: number, factor: number) {
    const next = Math.min(this.#maxScale, Math.max(this.#minScale, this.scale * factor));
    const applied = next / this.scale;
    if (applied === 1) return;
    this.x = px - (px - this.x) * applied;
    this.y = py - (py - this.y) * applied;
    this.scale = next;
    this.#notify();
  }

  /** Fit a content-space rect into the element, with optional padding. */
  fit(cx: number, cy: number, cw: number, ch: number, pad = 0) {
    const r = this.#rect;
    if (!r) return;
    const vw = r.width - pad * 2;
    const vh = r.height - pad * 2;
    const s = Math.min(vw / cw, vh / ch);
    const clamped = Math.min(this.#maxScale, Math.max(this.#minScale, s));
    this.scale = clamped;
    this.x = pad + (vw - cw * clamped) / 2 - cx * clamped;
    this.y = pad + (vh - ch * clamped) / 2 - cy * clamped;
    this.#notify();
  }

  #notify() {
    this.#onChange?.(this.transform);
  }

  // --- attachment ----------------------------------------------------------

  attach: Attachment<HTMLElement> = (el) => {
    const rectOf = () => (this.#rect ??= el.getBoundingClientRect());
    const invalidate = () => { this.#rect = null; };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();

      const unit =
        e.deltaMode === 1 ? this.#lineHeight :
        e.deltaMode === 2 ? el.clientHeight :
        1;

      const dx = e.deltaX * unit;
      const dy = e.deltaY * unit;

      if (e.ctrlKey || e.metaKey) {
        // Touchpad pinch arrives as wheel + synthetic ctrlKey.
        const r = rectOf();
        this.zoomAt(
          e.clientX - r.left,
          e.clientY - r.top,
          Math.exp(-dy * this.#zoomSpeed),
        );
        return;
      }

      // Mouse wheels emit sparse, large, integral deltas; touchpads emit
      // many small (often fractional) ones. Separate speeds, since one
      // factor never feels right for both.
      const looksLikeWheel = Math.abs(dy) >= 50 && Number.isInteger(e.deltaY);
      const k = looksLikeWheel ? this.#wheelPanSpeed : this.#panSpeed;

      this.panBy(-dx * k, -dy * k);
    };

    const onPointerDown = (e: PointerEvent) => {
      if (e.button !== 0 && e.button !== 1) return;
      this.#dragId = e.pointerId;
      this.#lastX = e.clientX;
      this.#lastY = e.clientY;
      el.setPointerCapture(e.pointerId);
    };

    const onPointerMove = (e: PointerEvent) => {
      if (e.pointerId !== this.#dragId) return;
      this.panBy(e.clientX - this.#lastX, e.clientY - this.#lastY);
      this.#lastX = e.clientX;
      this.#lastY = e.clientY;
    };

    const onPointerUp = (e: PointerEvent) => {
      if (e.pointerId !== this.#dragId) return;
      el.releasePointerCapture(e.pointerId);
      this.#dragId = null;
    };

    // Rect caching: getBoundingClientRect forces layout, and wheel events
    // fire fast during a pinch.
    const ro = new ResizeObserver(invalidate);
    ro.observe(el);

    el.addEventListener('wheel', onWheel, { passive: false });
    el.addEventListener('pointerdown', onPointerDown);
    el.addEventListener('pointermove', onPointerMove);
    el.addEventListener('pointerup', onPointerUp);
    el.addEventListener('pointercancel', onPointerUp);
    window.addEventListener('scroll', invalidate, true);
    window.addEventListener('resize', invalidate);

    rectOf();

    return () => {
      ro.disconnect();
      el.removeEventListener('wheel', onWheel);
      el.removeEventListener('pointerdown', onPointerDown);
      el.removeEventListener('pointermove', onPointerMove);
      el.removeEventListener('pointerup', onPointerUp);
      el.removeEventListener('pointercancel', onPointerUp);
      window.removeEventListener('scroll', invalidate, true);
      window.removeEventListener('resize', invalidate);
      this.#rect = null;
      this.#dragId = null;
    };
  };
}