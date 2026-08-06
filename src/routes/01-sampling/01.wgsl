// input texture
// output texture (framebuffer)
// sampling mode
// scaling: x, y

const SAMPLING_NEAREST: u32 = 0;
const SAMPLING_BILINEAR: u32 = 1;
const SAMPLING_BICUBIC: u32 = 2;

struct Settings {
    sampling_mode: u32,
    sourceSize: vec2<f32>,
    scale: vec2<f32>,
    offset: vec2<f32>,
}

// basically pushConstants
var<immediate> settings: Settings;
@group(0) @binding(0) var source_image: texture_storage_2d<rgba8unorm, read>;

const vertices = array<vec2<f32>, 6>(
    vec2(-1, -1),
    vec2(1, -1),
    vec2(-1, 1),
    vec2(1, 1),
    vec2(-1, 1),
    vec2(1, -1),
);

@vertex
fn vertexMain(
    @builtin(vertex_index) index: u32
) -> @builtin(position) vec4<f32> {
    return vec4(vertices[index], 0, 1);
}

@fragment
fn fragmentMain(@builtin(position) position: vec4<f32>) -> @location(0) vec4<f32> {
    // map to image space
    let pos = (position.xy - settings.offset) * settings.scale;

    // if position out of bounds
    if any(pos > (settings.sourceSize - 1)) || any(pos < vec2(0)) {
        return vec4(0);
    }

    switch settings.sampling_mode {
        case SAMPLING_NEAREST, default: {
            // this is becuased `round` is actually `round to nearest even number` bruh
            let rounded = vec2<u32>(floor(pos + 0.5));
            let pixel = textureLoad(source_image, rounded);
            return pixel;
        }

        case SAMPLING_BILINEAR: {
            let t = fract(pos);
            let p0 = vec2<u32>(pos);
            let p1 = vec2<u32>(pos) + vec2(0, 1);
            let p2 = vec2<u32>(pos) + vec2(1, 0);
            let p3 = vec2<u32>(pos) + 1;
            // no bounds check

            // x1 weight is t.x, x2 -> 1 - t.x
            let s0 = textureLoad(source_image, p0);
            let s1 = textureLoad(source_image, p1);
            let s2 = textureLoad(source_image, p2);
            let s3 = textureLoad(source_image, p3);

            return mix(
                mix(s0, s1, t.y), // mix is lerp
                mix(s2, s3, t.y),
                t.x
            );
        }

        case SAMPLING_BICUBIC: {
            let t = fract(pos);
            let o = vec2<u32>(pos);

            var rows: array<vec4<f32>, 4>;
            for (var x = 0u; x <= 3; x++) {
                var cols: array<vec4<f32>, 4>;
                for (var y = 0u; y <= 3; y++) {
                    cols[y] = textureLoad(source_image, vec2(o.x + x - 1, o.y + y - 1));
                }
                rows[x] = sampleCubic(cols[0], cols[1], cols[2], cols[3], t.y);
            }

            return sampleCubic(rows[0], rows[1], rows[2], rows[3], t.x);
        }
    }
}

// use 2 point + 2 slope to triangulate the function
// sample 4 point anyway to get the slope
fn sampleCubic(p0: vec4<f32>, p1: vec4<f32>, p2: vec4<f32>, p3: vec4<f32>, t: f32) -> vec4<f32> {
    let m1 = (p2 - p0) / 2;
    let m2 = (p3 - p1) / 2;

    let a = 2 * (p1 - p2) + m1 + m2;
    let b = 3 * (p2 - p1) - m2 - 2 * m1;
    let c = m1;
    let d = p1;

    return a * pow(t, 3) + b * pow(t, 2) + c * t + d;
}

// TODO: 
fn linearized(c: vec3<f32>) -> vec3<f32> {
    return c;
}

