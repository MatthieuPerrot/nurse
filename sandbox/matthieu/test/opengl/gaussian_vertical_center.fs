# version 120
varying vec2 texture_coordinate;
uniform sampler2D sampler;
const int n = 11;
//const int n = 21;
vec4 tex;
vec2 s; 
float d;
float w;
float sum;
const float size = 0.25;
const vec2 center = vec2(0.5, 0.5); 

const float filter2[11] = float[](0.00876415,  0.02699548,  0.0647588 ,  0.12098536,  0.17603266, 0.19947114,  0.17603266,  0.12098536,  0.0647588 ,  0.02699548, 0.00876415);
const float filter5[21] = float[](0.01079819,  0.01579003,  0.02218417,  0.02994549,  0.03883721, 0.04839414,  0.05793831,  0.06664492,  0.07365403,  0.07820854, 0.07978846,  0.07820854,  0.07365403,  0.06664492,  0.05793831, 0.04839414,  0.03883721,  0.02994549,  0.02218417,  0.01579003, 0.01079819);

void main(void)
{
	tex = vec4(0., 0., 0., 0.);
	d = distance(center, texture_coordinate.st);
	w = 1 - exp(-d * d / (0.5 * size * size));
	sum = 0.;
	if (w > 0.1) // to prevent overflow
	{
		for (int i = 0; i < n; ++i)
		{
			s = vec2((float(i) - (n - 1) / 2) / 640., 0.);
			tex += pow(filter2[i], 1./w) * texture2D(sampler,
					texture_coordinate.st + s);
			sum += pow(filter2[i], 1./w);
		}
	}
	else
	{
		tex += texture2D(sampler, texture_coordinate.st);
		sum = 1.;
	}
	gl_FragColor = vec4(tex.xyz / sum, 1.); 
}
