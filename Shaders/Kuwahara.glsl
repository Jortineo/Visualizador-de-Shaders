#version 330

// Recibido desde tu VERTEX_SHADER de ModernGL
in vec2 v_texcoord;
out vec4 f_color;

// Uniform configurado por tu clase Renderizador
uniform sampler2D u_screen_texture;

// Parámetros del filtro Kuwahara
const int RADIUS = 5;          
const float Q_PARAMETER = 8.0; 
const float HARDNESS = 1.0;    

float getLuminance(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

void main() {
    // CORRECCIÓN DE INVERSIÓN VERTICAL:
    // Volteamos el eje Y de la coordenada de lectura para corregir el desfase Pygame vs OpenGL.
    vec2 flippedTexcoord = vec2(v_texcoord.x, 1.0 - v_texcoord.y);

    // Detecta el tamaño del búfer de captura automáticamente
    ivec2 texSize = textureSize(u_screen_texture, 0);
    vec2 invTexSize = 1.0 / vec2(texSize);
    
    // 1. Tensor de estructura simplificado (Gradientes locales utilizando la coordenada corregida)
    float c  = getLuminance(texture(u_screen_texture, flippedTexcoord).rgb);
    float t  = getLuminance(texture(u_screen_texture, flippedTexcoord + vec2(0.0, invTexSize.y)).rgb);
    float b  = getLuminance(texture(u_screen_texture, flippedTexcoord - vec2(0.0, invTexSize.y)).rgb);
    float r  = getLuminance(texture(u_screen_texture, flippedTexcoord + vec2(invTexSize.x, 0.0)).rgb);
    float l  = getLuminance(texture(u_screen_texture, flippedTexcoord - vec2(invTexSize.x, 0.0)).rgb);
    
    float gX = (r - l) / 2.0;
    float gY = (t - b) / 2.0;
    
    // Calcular el ángulo del flujo de los bordes
    float angle = atan(gY, gX) + 3.14159265 / 2.0; 
    
    float cosA = cos(angle);
    float sinA = sin(angle);
    mat2 R = mat2(cosA, -sinA, sinA, cosA);
    
    // Inicializar contenedores para los 4 cuadrantes del Kuwahara
    vec3 m[4] = vec3[](vec3(0.0), vec3(0.0), vec3(0.0), vec3(0.0)); // Medias
    vec3 s[4] = vec3[](vec3(0.0), vec3(0.0), vec3(0.0), vec3(0.0)); // Varianzas
    float n[4] = float[](0.0, 0.0, 0.0, 0.0);                      // Contador de muestras

    // 2. Muestreo adaptativo rotando según la orientación del borde
    for (int j = -RADIUS; j <= RADIUS; ++j) {
        for (int i = -RADIUS; i <= RADIUS; ++i) {
            // Rotar coordenadas para seguir la forma geométrica
            vec2 v = R * vec2(float(i), float(j));
            vec2 offset = v * invTexSize;
            
            // Muestreamos usando la coordenada base ya volteada
            vec3 color = texture(u_screen_texture, flippedTexcoord + offset).rgb;
            
            // Clasificar en cuál de los 4 sectores cae tras la rotación
            int k = 0;
            if (i >= 0 && j >= 0) k = 0;
            else if (i <= 0 && j >= 0) k = 1;
            else if (i <= 0 && j <= 0) k = 2;
            else if (i >= 0 && j <= 0) k = 3;
            
            m[k] += color;
            s[k] += color * color;
            n[k] += 1.0;
        }
    }

    // 3. Selección y filtrado inteligente basado en varianza
    vec4 finalColor = vec4(0.0);
    float sumWeights = 0.0;

    for (int k = 0; k < 4; ++k) {
        m[k] /= n[k];
        s[k] = abs(s[k] / n[k] - m[k] * m[k]);
        
        float sigma2 = s[k].r + s[k].g + s[k].b;
        
        // Función sigmoide para ponderar
        float w = 1.0 / (1.0 + pow(HARDNESS * 1000.0 * sigma2, Q_PARAMETER / 2.0));
        
        finalColor += vec4(m[k] * w, w);
        sumWeights += w;
    }

    // Retornar color final derecho y estilizado
    f_color = vec4(finalColor.rgb / sumWeights, 1.0);
}
