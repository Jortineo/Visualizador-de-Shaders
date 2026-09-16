#version 330 core

// La textura que contiene los píxeles de lo que hay detrás de la ventana
uniform sampler2D u_screen_texture; 

// Coordenadas UV interpoladas desde el Vertex Shader (de 0.0 a 1.0)
in vec2 v_texcoord; 

// El color final invertido que se enviará al monitor
out vec4 fragColor;

void main() {
    // Invertimos la coordenada Y de la UV para corregir el volcado de OpenGL
    vec2 uv_corregida = vec2(v_texcoord.x, 1.0 - v_texcoord.y);

    // 1. Muestrear usando la UV corregida
    vec4 color_original = texture(u_screen_texture, uv_corregida);
    
    // 2. Invertir los canales RGB restándolos de 1.0
    vec3 color_negativo = 1.0 - color_original.rgb;
    
    // 3. Asignar el resultado al búfer de salida
    fragColor = vec4(color_negativo, color_original.a);
}
