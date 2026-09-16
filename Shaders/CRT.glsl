#version 330 core

uniform sampler2D u_screen_texture; 
in vec2 v_texcoord; 
out vec4 fragColor;

void main() {
    // 1. Corregimos la Y invertida de OpenGL
    vec2 uv = vec2(v_texcoord.x, 1.0 - v_texcoord.y);
    
    // 2. EFECTO LUPA (Distorsión de lente esférica)
    // Nos centramos en el medio de la pantalla (0.0 en el centro)
    vec2 centro = uv - 0.5;
    float distancia = length(centro);
    
    // Si el píxel está cerca del centro, lo empujamos hacia afuera
    if (distancia < 0.5) {
        // Fórmula matemática para curvar las coordenadas
        centro *= (distancia * distancia * 2.0 + 0.5) / 0.5;
        uv = centro + 0.5;
    }
    
    // 3. EFECTO PIXEL ART (Filtro de mosaico)
    // Reducimos la resolución efectiva dividiendo y multiplicando por un número fijo
    float tamano_pixel = 120.0; // Cuanto más bajo, más grandes los píxeles
    uv.x = floor(uv.x * tamano_pixel) / tamano_pixel;
    uv.y = floor(uv.y * tamano_pixel) / tamano_pixel;
    
    // 4. Muestrear el color final distorsionado y pixelado
    vec4 color_final = texture(u_screen_texture, uv);
    
    // Le añadimos un ligero toque verdoso estilo GameBoy antigua
    color_final.g *= 1.2;
    
    fragColor = color_final;
}
