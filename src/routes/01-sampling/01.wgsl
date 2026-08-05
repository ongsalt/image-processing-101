// input texture
// output texture (framebuffer)
// sampling mode
// scaling: x, y
const SAMPLING_NEAREST: u32 = 0;
const SAMPLING_BILINEAR: u32 = 1;
const SAMPLING_BICUBIC: u32 = 2;

struct PushConstants {
    sampling_mode: u32,
    sourceSize: vec2<u32>,
    size: vec2<u32>,
    offset: vec2<u32>,
}

struct VertexOutput {
    @builtin(position) position: vec4<f32>}

const vertices = array<vec2<f32>, 6>(
    vec2(0, 0),
    vec2(1, 0),
    vec2(0, 1),
    vec2(1, 1),
    vec2(0, 1),
    vec2(1, 0),
);

@vertex
fn vertex_main(
    @builtin(vertex_index) vertex_index: u32
) -> VertexOutput {
    let v = vertices[vertex_index];

    return VertexOutput(
        vec4(v, 0, 1),
    );
}

@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
    return input.color;
}

// TODO: 
fn linearized(c: vec3<f32>) -> vec3<f32> {
    return c;
}

