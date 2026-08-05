
struct Vertex {
    position: vec2<f32>,
    color: vec4<f32>,
}

struct VertexOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) color: vec4<f32>,
}

const vertices = array<Vertex, 3>(
    Vertex(vec2(0, 0.5), vec4(1, 0, 0, 1)),
    Vertex(vec2(-0.5, -0.5), vec4(0, 1, 0, 1)),
    Vertex(vec2(0.5, -0.5), vec4(0, 0, 1, 1)),
);

@vertex
fn vertex_main(
    @builtin(vertex_index) vertex_index: u32
) -> VertexOutput {
    let v = vertices[vertex_index];

    return VertexOutput(
        vec4(v.position, 0, 1),
        v.color
    );
}

@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
    return input.color;
}