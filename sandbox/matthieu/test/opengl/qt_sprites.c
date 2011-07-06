#include <iostream>
#include <stdio.h>
#include "GL/gl.h"
#include "GL/glut.h"
#include "string.h"

int ExtensionSupportee(const char *nom)
{
	const char *extensions = (char *) glGetString(GL_EXTENSIONS);

	if (strstr(extensions, nom) != NULL)
		return 1;
	else
	{
		fprintf(stderr, "extension %s non supportee\n", nom);
		return 0;
	}
}

int main(int argc, char *argv[])
{
	glutInit(&argc, argv);
	glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH);
	glutInitWindowSize(640, 480);
	glutInitWindowPosition(0, 0);
	int	window = glutCreateWindow("title");


	

	glEnable(GL_ARB_shader_objects);
	glEnable(GL_FRAGMENT_PROGRAM_ARB);

	char *c = NULL;

	c = (char *) glGetString(GL_SHADING_LANGUAGE_VERSION_ARB);
	if (c)
	{
		std::cout << "GL_SHADING_LANGUAGE_VERSION_ARB = " << c
			<< std::endl;
	}
	c = (char *) glGetString(GL_PROGRAM_ERROR_POSITION_ARB);
	if (c)
	{
		std::cout << "GL_PROGRAM_ERROR_POSITION_ARB = " << c
			<< std::endl;
	}
	c = (char *) glGetString(GL_SHADE_MODEL);
	if (c)
	{
		std::cout << "GL_SHADE_MODEL = " << c
			<< std::endl;
	}
	c = (char *) glGetString(GL_SHADER_TYPE);
	if (c)
	{
		std::cout << "GL_SHADER_TYPE = " << c
			<< std::endl;
	}
	c = (char *) glGetString(GL_SHADER_OBJECT_ARB);
	if (c)
	{
		std::cout << "GL_SHADER_OBJECT_ARB = " << c
			<< std::endl;
	}
	c = (char *) glGetString(GL_VENDOR);
	if (c)
	{
		std::cout << "GL_VENDOR = " << c
			<< std::endl;
	}
	c = (char *) glGetString(GL_EXTENSIONS);
	if (c)
	{
		std::cout << "GL_EXTENSIONS = " << c
			<< std::endl;
	}
}
