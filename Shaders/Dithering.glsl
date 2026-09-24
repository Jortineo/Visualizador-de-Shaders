#version 330

// Recibido desde tu VERTEX_SHADER de ModernGL
in vec2 v_texcoord;
out vec4 f_color;

// Uniform configurado por tu clase Renderizador
uniform sampler2D u_screen_texture;

// Parámetros del filtro Dithering
const float COLOR_LEVELS = 4.0; // Cantidad de tonos por canal (menor número = más retro)

// Sintaxis explícita float[16] para evitar fallos de inicialización en GLSL 330
const float bayerMatrix[16] = float[16](
     0.0 / 16.0,  8.0 / 16.0,  2.0 / 16.0, 10.0 / 16.0,
    12.0 / 16.0,  4.0 / 16.0, 14.0 / 16.0,  6.0 / 16.0,
     3.0 / 16.0, 11.0 / 16.0,  1.0 / 16.0,  9.0 / 16.0,
    15.0 / 16.0,  7.0 / 16.0, 13.0 / 16.0,  5.0 / 16.0
);

void main() {
    // CORRECCIÓN DE INVERSIÓN VERTICAL:
    vec2 flippedTexcoord = vec2(v_texcoord.x, 1.0 - v_texcoord.y);

    // 1. Obtener el color original usando la coordenada corregida
    vec4 originalColor = texture(u_screen_texture, flippedTexcoord);
    
    // 2. Detectar el tamaño del búfer de captura automáticamente
    ivec2 texSize = textureSize(u_screen_texture, 0);
    
    // 3. Obtener la posición entera del píxel en pantalla de forma segura
    int px = int(flippedTexcoord.x * float(texSize.x));
    int py = int(flippedTexcoord.y * float(texSize.y));
    
    // Operación módulo asegurada con enteros positivos
    int x = px % 4;
    int y = py % 4;
    
    // 4. Obtener el valor de dispersión de la matriz
    float threshold = bayerMatrix[y * 4 + x];
    
    // 5. Aplicar el dithering a los canales RGB
    vec3 ditheredColor = originalColor.rgb + (vec3(threshold) - 0.5) * (1.0 / COLOR_LEVELS);
    
    // Evitamos valores negativos antes del floor clamping para que no colapse a negro puro
    ditheredColor = clamp(ditheredColor, 0.0, 1.0);
    
    // 6. Cuantización (Reducción de la paleta)
    ditheredColor = floor(ditheredColor * COLOR_LEVELS) / COLOR_LEVELS;
    
    // Retornar color final convertido a formato BGRA (Inversión de canales R y B)
    f_color = vec4(ditheredColor.b, ditheredColor.g, ditheredColor.r, originalColor.a);
}
