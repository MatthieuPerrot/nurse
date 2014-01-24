varying vec2 texture_coordinate;
uniform sampler2D sampler;
vec4 tex;
vec3 mean;
const vec3 white = vec3(255., 250., 192.) / 255.;
const int width = 640;
const int height = 480;

void main(void)
{
	tex = texture2D(sampler, texture_coordinate.xy);

	if (gl_FragCoord.x > (width / 2.))
	{
		//float grey = color.r*0.299 + color.g*0.587 + color.b*0.114;
		mean = vec3((tex.r + tex.g + tex.b) / 3.);
		if (gl_FragCoord.y > (height / 2.)) // grey tone
		{
			gl_FragColor = vec4(mean, tex.a);
		}
		else // sepia tone
		{
			// method M$
			if (gl_FragCoord.x > (3. * width / 4.))
			{
				gl_FragColor = clamp(vec4(
				tex.r * 0.393 + tex.g * 0.769 + tex.b * 0.189,
				tex.r * 0.349 + tex.g * 0.686 + tex.b * 0.168,
				tex.r * 0.272 + tex.g * 0.534 + tex.b * 0.131,
				tex.a), 0., 1.);
			}
			else // method based on a brownish palette
			{
				gl_FragColor = vec4(mean * white, tex.a);
			}
		}
	}
	else
	{
		gl_FragColor = texture2D(sampler, texture_coordinate);
	}
}