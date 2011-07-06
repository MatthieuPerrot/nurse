
void main(void)
{
	//gl_FragColor = vec4(gl_FragCoord.x / 800., gl_FragCoord.y / 600., 0., 1.0);

	//gl_FragColor = vec4(gl_Color.r, gl_Color.g, gl_Color.b, 1.0);
	gl_FragColor = (gl_Color.r + gl_Color.g + gl_Color.b) / 3.;
}
