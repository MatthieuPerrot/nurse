# version 120
varying vec2 texture_coordinate;
uniform sampler2D sampler;
const int n = 11;
//const int n = 21;
vec4 tex;
vec2 s; 

const float filter2[11] = float[](0.00876415,  0.02699548,  0.0647588 ,  0.12098536,  0.17603266, 0.19947114,  0.17603266,  0.12098536,  0.0647588 ,  0.02699548, 0.00876415);
const float filter5[21] = float[](0.01079819,  0.01579003,  0.02218417,  0.02994549,  0.03883721, 0.04839414,  0.05793831,  0.06664492,  0.07365403,  0.07820854, 0.07978846,  0.07820854,  0.07365403,  0.06664492,  0.05793831, 0.04839414,  0.03883721,  0.02994549,  0.02218417,  0.01579003, 0.01079819);

void main(void)
{
	tex = vec4(0., 0., 0., 0.);

	for (int i = 0; i < n; ++i)
	{
		s = vec2(0., (float(i) - (n - 1) / 2) / 480.);
		tex += filter2[i] * texture2D(sampler,
				texture_coordinate.st + s);
	}
	gl_FragColor = vec4(tex.xyz, 1.);
}
