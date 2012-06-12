'''
Created on 15/06/2011

@author: adam

TODO: use resource locations
http://www.pyglet.org/doc/programming_guide/loading_resources.html
'''

import math
import time
import random

from pyglet.gl import *
import pyglet
import numpy

import pygly.window
import pygly.gl
import pygly.sorter
from pygly.ratio_viewport import RatioViewport
from pygly.projection_view_matrix import ProjectionViewMatrix
from pygly.scene_node import SceneNode
from pygly.camera_node import CameraNode
from pygly.render_callback_node import RenderCallbackNode
from pygly.fps_controller import FPS_Controller
from pygly.input.keyboard import Keyboard
from pygly.input.mouse import Mouse

import cube

# over-ride the default pyglet idle loop
import pygly.monkey_patch
pygly.monkey_patch.patch_idle_loop()


class Application( object ):
    
    def __init__( self ):
        super( Application, self ).__init__()
        
        # setup our opengl requirements
        config = pyglet.gl.Config(
            depth_size = 16,
            double_buffer = True
            )

        # create our window
        self.window = pyglet.window.Window(
            fullscreen = False,
            width = 1024,
            height = 768,
            resizable = True,
            config = config
            )

        # create a viewport
        self.viewport = RatioViewport(
            self.window,
            [ [0.0, 0.0], [1.0, 1.0] ]
            )

        # create our input devices
        self.keyboard = Keyboard( self.window )
        self.mouse = Mouse( self.window )

        # setup our scene
        self.setup_scene()
        
        # setup our update loop the app
        # we'll render at 60 fps
        frequency = 60.0
        self.update_delta = 1.0 / frequency
        # use a pyglet callback for our render loop
        pyglet.clock.schedule_interval(
            self.step,
            self.update_delta
            )

        # display the current FPS
        self.fps_display = pyglet.clock.ClockDisplay()
        
        print "Rendering at %iHz" % int(frequency)

    def setup_scene( self ):
        # create a list of renderables
        self.renderables = []

        # create a scene
        self.scene_node = SceneNode( 'root' ) 
        
        # create a camera and a view matrix
        self.view_matrix = ProjectionViewMatrix(
            self.viewport.aspect_ratio,
            fov = 45.0,
            near_clip = 1.0,
            far_clip = 200.0
            )
        # create a camera
        self.camera = CameraNode(
            'camera',
            self.view_matrix
            )
        self.scene_node.add_child( self.camera )

        # move the camera so we can see the grid
        self.camera.translate_inertial(
            [ 0.0, 0.0, 80.0 ]
            )
        # rotate the camera so it is pointing down
        self.camera.rotate_object_x( -math.pi / 4.0 )
        
        # assign a camera controller
        # we'll use the FPS camera for this one
        self.camera_controller = FPS_Controller()
        self.camera_controller.scene_node = self.camera

        # create a number of cubes
        num_cubes = 20
        cube_distance = 50
        positions = numpy.random.rand( num_cubes, 3 )

        # make all the cubes sit in the Y=0 plane
        positions[ :, 1 ] = 0.0

        # set the distance of the cubes
        positions *= cube_distance

        for position in positions:
            node = RenderCallbackNode(
                'cube',
                cube.initialise,
                cube.render
                )
            node.inertial_translation = position
            self.scene_node.add_child( node )
            self.renderables.append( node )

        # create a list of colours that we will use to
        # render each object
        # this will let us know the sort order
        self.colours = numpy.linspace( 0.0, 1.0, num_cubes )
        # repeat the values 3 times each
        self.colours = self.colours.repeat( 3 )
        # reshape into colour vectors
        self.colours.shape = ( num_cubes, 3 )

    def run( self ):
        pyglet.app.run()
    
    def step( self, dt ):
        self.move_camera( dt )

        # render the scene
        self.render()

        # render the fps
        self.fps_display.draw()
        
        # display the frame buffer
        self.window.flip()

    def move_camera( self, dt ):
        # update the Camera
        camera_speed = 40.0
        
        # handle input
        # this looks complex, but all we're doing
        # is checking for WASD / Arrows
        # and then sending forward, backward, etc
        # to the camera controller with an amount that
        # is scaled by the current time delta

        # move forward
        if self.keyboard[ self.keyboard.keys.W ] or self.keyboard[ self.keyboard.keys.UP ]:
            self.camera_controller.translate_forward( camera_speed * dt )

        # move backward
        if self.keyboard[ self.keyboard.keys.S ] or self.keyboard[ self.keyboard.keys.DOWN ]:
            self.camera_controller.translate_backward( camera_speed * dt )

        # move right
        if self.keyboard[ self.keyboard.keys.D ] or self.keyboard[ self.keyboard.keys.RIGHT ]:
            self.camera_controller.translate_right( camera_speed * dt )

        # move right
        if self.keyboard[ self.keyboard.keys.A ] or self.keyboard[ self.keyboard.keys.LEFT ]:
            self.camera_controller.translate_left( camera_speed * dt )

        # move up
        if self.keyboard[ self.keyboard.keys.SPACE ]:
            self.camera_controller.translate_up( camera_speed * dt )

        # move up
        if self.keyboard[ self.keyboard.keys.LSHIFT ]:
            self.camera_controller.translate_down( camera_speed * dt )
        
        # handle camera rotation
        # get the relative movement of the mouse
        # since the last frame
        mouse_relative = self.mouse.relative_position

        # the base movement speed we use for
        # scaling with the mouse movements
        # this value just feels about right
        mouse_speed = 0.006
        
        # scale the mouse movement by the relative value
        # DON'T multiply by the time delta here
        # think about it, it's not what you want!
        frame_pitch = math.pi * mouse_speed * mouse_relative[ 1 ]
        frame_yaw = -math.pi * mouse_speed * mouse_relative[ 0 ]
        
        # check for mouse inverts, for us freaks...
        # WE HAVE RIGHTS TOO!
        invert_y = True
        if invert_y == True:
            frame_pitch = -frame_pitch
        
        # pass the mouse movement to the camera controller
        self.camera_controller.orient( pitch = frame_pitch, yaw = frame_yaw )
        
        # reset our mouse relative position
        # we should do this each time we take a reading
        # or the delta will continue to accumulate
        self.mouse.clear_delta()

    def set_gl_state( self ):
        # enable z buffer
        glEnable( GL_DEPTH_TEST )

        # enable smooth shading
        glShadeModel( GL_SMOOTH )

        # rescale only normals for lighting
        glEnable( GL_RESCALE_NORMAL )

        # enable scissoring for viewports
        glEnable( GL_SCISSOR_TEST )

        # enable back face culling
        glEnable( GL_CULL_FACE )
        glCullFace( GL_BACK )

    def render( self ):
        #
        # setup
        #

        # set our window
        self.window.switch_to()

        # activate our viewport
        self.viewport.switch_to()

        # scissor to our viewport
        self.viewport.scissor_to_viewport()

        # setup our viewport properties
        glPushAttrib( GL_ALL_ATTRIB_BITS )
        self.set_gl_state()

        # update the view matrix aspect ratio
        self.camera.view_matrix.aspect_ratio = self.viewport.aspect_ratio

        # apply our view matrix and camera translation
        self.camera.view_matrix.push_view_matrix()
        self.camera.push_model_view()

        #
        # render
        #

        # clear our frame buffer and depth buffer
        glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )

        # sort our renderables
        positions = [ obj.world_translation for obj in self.renderables ]

        sorted_renderables = pygly.sorter.sort_front_to_back(
            self.camera.world_translation,
            -(self.camera.object_z_axis),
            self.renderables,
            positions
            )

        # render each object
        for renderable, colour in zip(sorted_renderables, self.colours):
            # set our colour
            glColor3f(
                colour[ 0 ],
                colour[ 1 ],
                colour[ 2 ],
                )
            # render the object
            renderable.render()

        #
        # tear down
        #

        # pop our view matrix and camera translation
        self.camera.pop_model_view()
        self.camera.view_matrix.pop_view_matrix()

        # pop our viewport attributes
        glPopAttrib()

        #
        # reset state
        #

        # set our viewport to the entire window
        pygly.gl.set_scissor(
            pygly.window.create_rectangle( self.window )
            )
        pygly.gl.set_viewport(
            pygly.window.create_rectangle( self.window )
            )

def main():
    # create app
    app = Application()
    app.run()
    app.window.close()


if __name__ == "__main__":
    main()
