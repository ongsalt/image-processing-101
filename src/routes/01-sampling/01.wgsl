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

var<immediate> settings: Settings;
@group(0) @binding(0) var source_image: texture_storage_2d<rgba8unorm, read>;

struct VertexOutput {
    @builtin(position) position: vec4<f32>,
}

const vertices = array<vec2<f32>, 6>(
    vec2(-1, -1),
    vec2(1, -1),
    vec2(-1, 1),
    vec2(1, 1),
    vec2(-1, 1),
    vec2(1, -1),
);

@vertex
fn vertex_main(
    @builtin(vertex_index) vertex_index: u32
) -> VertexOutput {
    let v = vertices[vertex_index];

    return VertexOutput(vec4(v, 0, 1));
}

@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
    let pos = (input.position.xy - settings.offset) * settings.scale;

    let rounded = vec2<u32>(floor(pos + 0.5)); // this is becuased `round` is `round to nearest even number` bruh
    // if position out of bounds
    if any(pos > (settings.sourceSize - 1)) || any(pos < vec2(0)) {
        return vec4(0);
    }

    if settings.sampling_mode == SAMPLING_NEAREST {
        let pixel = textureLoad(source_image, rounded);
        return pixel;
    }

    let t = fract(pos);
    let p0 = vec2<u32>(pos);
    let p1 = vec2<u32>(pos) + vec2(0, 1);
    let p2 = vec2<u32>(pos) + vec2(1, 0);
    let p3 = vec2<u32>(pos) + 1;

    // x1 weight is t.x, x2 -> 1 - t.x
    let s0 = textureLoad(source_image, p0);
    let s1 = textureLoad(source_image, p1);
    let s2 = textureLoad(source_image, p2);
    let s3 = textureLoad(source_image, p3);

    return mix(
        mix(s0, s1, t.y),
        mix(s2, s3, t.y),
        t.x
    );
}

// TODO: 
fn linearized(c: vec3<f32>) -> vec3<f32> {
    return c;
}

