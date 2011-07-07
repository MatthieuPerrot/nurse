varying vec2 texture_coordinate;
uniform sampler2D sampler;
vec4 tex;
uniform vec3 mean;

void main(void)
{
	//gl_FragColor = vec4(gl_Color.r, gl_Color.g, gl_Color.b, 1.0);
	//gl_FragColor = (gl_Color.r + gl_Color.g + gl_Color.b) / 3.;
	tex = texture2D(sampler, texture_coordinate.xy);
	if (gl_FragCoord.x > 400.)
	{
		mean = (tex.r + tex.g + tex.b) / 3.;
		gl_FragColor = vec4(mean, tex.a);
	}
	else
	{
		gl_FragColor = texture2D(sampler, texture_coordinate);
	}
}
