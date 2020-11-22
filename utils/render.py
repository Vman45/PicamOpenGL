import time

# pi 3b+ only support OpenGL 1.10, 1.20, ES 1.0
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from utils import fps

class BaseRenderer:
    def __init__(self, queue_helper):
        self.fps_counter = fps.FPSCounter()
        self.queue_helper = queue_helper

    def render(self, *_args, **_kwargs):
        raise NotImplementedError()

class OpenGLRenderer(BaseRenderer):
    def __init__(self, queue_helper, img_width=None, img_height=None, *_args, **_kwargs):
        BaseRenderer.__init__(self, queue_helper)
        self.img_w = img_width
        self.img_h = img_height

        self.fps_counter.update_render(
            # TODO: update render_func
            render_func=(lambda f : print("FPS: {}".format(f)))
        )

        self.buf = None
        self.result = None

        self.line_thickness = 5
        self.line_z_pos = 0.5

    def _wait_img(self):
        message = self.queue_helper.get()
        self.fps_counter.add()
        self.buf = message.get_buf()
        self.result = message.get_result()
        glutPostRedisplay()

    def _key_press(self, key, *args):
        # Link: https://butterflyofdream.wordpress.com/2016/04/27/pyopengl-keyboard-wont-respond/
        pressed = key.decode("utf-8")
        if pressed == 'q' or pressed == '\x1b':
            sys.exit(0)

    def _update_tex(self):
        # Draw only when there is something
        if self.buf is None:
            return
        # Apply texture
        glTexImage2D(GL_TEXTURE_2D, 0, 3, self.img_w, self.img_h,
            0, GL_RGB, GL_UNSIGNED_BYTE, self.buf
        )

    def _draw_bbox(self):
        # Draw only when there is something
        if self.result is None:
            return
        # Loop all result
        for entry in self.result:
            # coord = (x1, y1, x2, y2) OR index = (0, 1, 2, 3)
            # seq -> (x1, y1), (x1, y2), (x2, y2), (x2, y1), (x1, y1)
            glBegin(GL_LINE_LOOP)
            glColor3f(0.0, 1.0, 0.0)
            glVertex3f(entry["boxes"][0], entry["boxes"][1], self.line_z_pos)
            glVertex3f(entry["boxes"][0], entry["boxes"][3], self.line_z_pos)
            glVertex3f(entry["boxes"][2], entry["boxes"][3], self.line_z_pos)
            glVertex3f(entry["boxes"][2], entry["boxes"][1], self.line_z_pos)
            glVertex3f(entry["boxes"][0], entry["boxes"][1], self.line_z_pos)
            glEnd()

    def _draw_rect(self):
        # Draw rect texture coordinates
        glBegin(GL_QUADS)
        glColor3f(1.0, 1.0, 1.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(-1.0, -1.0,  0.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( 1.0, -1.0,  0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( 1.0,  1.0,  0.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-1.0,  1.0,  0.0)
        glEnd()

    def _draw_scene(self):
        # Clear
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render
        self._update_tex()
        self._draw_rect()
        self._draw_bbox()

        # FPS related
        self.fps_counter.render_fps()

        glutSwapBuffers()

    def _init_gl(self):
        # Initialize GL
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glLineWidth(self.line_thickness)

    def render(self, width=1, height=1, title="Pi Camera OpenGL Renderer"):
        # setup and run OpenGL
        glutInit()
        glutInitDisplayMode(GLUT_RGB)
        glutInitWindowSize(width, height)
        glutInitWindowPosition(0, 0)
        glutCreateWindow(title)
        glutDisplayFunc(self._draw_scene)
        glutIdleFunc(self._wait_img)
        glutKeyboardFunc(self._key_press)
        self._init_gl()
        glutMainLoop()

class NullRenderer(BaseRenderer):
    '''
    Empty opengl implementation don't work, similar fps as OpenGLRenderer
    '''
    def __init__(self, queue_helper, *_args, **_kwargs):
        BaseRenderer.__init__(self, queue_helper)
        self.fps_counter.update_render(
            # Naive print
            render_func=(lambda f : print("FPS: {}".format(f)))
        )

    def render(self, *_args, **_kwargs):
        try:
            while True:
                _ = self.queue_helper.get()
                self.fps_counter.add()
                self.fps_counter.render_fps()
        except KeyboardInterrupt:
            # After ctrl + c
            return
