
struct Settings {
    gamma: f32,
    sourceSize: vec2<f32>,
    scale: vec2<f32>,
    offset: vec2<f32>,
}

var<immediate> settings: Settings;
@group(0) @binding(0) var texture: texture_2d<f32>;
@group(0) @binding(1) var s: sampler;

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

    let pixel = textureSample(texture, s, pos);
    return pixel;
}