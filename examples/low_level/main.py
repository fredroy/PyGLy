'''
Created on 03/03/2012

@author: adam
'''

import math

from pyglet.gl import *
import pyglet

import pygly.window
import pygly.gl
from pygly.projection_view_matrix import ProjectionViewMatrix
from pygly.scene_node import SceneNode
from pygly.render_callback_node import RenderCallbackNode
from pygly.camera_node import CameraNode

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

        # create a viewport that spans
        # the entire screen
        self.viewport = pygly.window.create_rectangle(
            self.window
            )

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
        # create a scene
        self.scene_node = SceneNode( 'root' )

        self.sn1 = SceneNode( 'sn1' )
        self.sn2 = SceneNode( 'sn2' )
        self.sn3 = SceneNode( 'sn3' )
        self.scene_node.add_child( self.sn1 )
        self.sn1.add_child( self.sn2 )
        self.sn2.add_child( self.sn3 )

        self.sn1.transform.scale = [2.0, 2.0, 2.0]
        self.sn2.transform.scale =  [0.5, 0.5, 0.5]
        self.sn3.transform.scale =  [2.0, 2.0, 2.0]

        # move our scene nodes
        self.sn1.transform.object.translate(
            [ 0.0,10.0, 0.0 ]
            )
        self.sn2.transform.object.translate(
            [10.0, 0.0, 0.0 ]
            )
        self.sn3.transform.object.translate(
            [ 5.0, 0.0, 0.0 ]
            )

        # rotate the scene so it is tilting forward
        self.sn1.transform.object.rotate_x( math.pi / 4.0 )

        # create a camera and a view matrix
        self.view_matrix = ProjectionViewMatrix(
            pygly.window.aspect_ratio( self.viewport ),
            fov = 45.0,
            near_clip = 1.0,
            far_clip = 200.0
            )
        self.camera = CameraNode(
            'camera',
            self.view_matrix
            )
        self.scene_node.add_child( self.camera )

        # move the camera so we're not inside
        # the root scene node's debug cube
        self.camera.transform.object.translate(
            [ 0.0, 20.0, 40.0 ]
            )

        # register our on_resize handler
        self.window.push_handlers(
            on_resize = self.on_resize
            )

    def run( self ):
        pyglet.app.run()

    def on_resize( self, width, height ):
        # update the viewport size
        self.viewport = pygly.window.create_rectangle(
            self.window
            )

        # update the view matrix aspect ratio
        self.camera.view_matrix.aspect_ratio = pygly.window.aspect_ratio(
            self.viewport
            )

    def step( self, dt ):
        # setup the scene
        # rotate the scene nodes about their vertical axis
        self.sn1.transform.object.rotate_y( dt )
        self.sn2.transform.object.rotate_y( dt )

        self.render()

        # render the fps
        self.fps_display.draw()

        # display the frame buffer
        self.window.flip()

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
        pygly.gl.set_viewport( self.viewport )
        # scissor to our viewport
        pygly.gl.set_scissor( self.viewport )

        # setup our viewport properties
        glPushAttrib( GL_ALL_ATTRIB_BITS )
        self.set_gl_state()

        # apply our view matrix and camera translation
        self.camera.view_matrix.push_view_matrix()
        self.camera.push_model_view()

        #
        # render
        #

        # clear our frame buffer and depth buffer
        glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )

        # render the scene node debug information
        self.scene_node.render_debug()

        #
        # tear down
        #

        # pop our view matrix and camera transforms
        self.camera.pop_model_view()
        self.camera.view_matrix.pop_view_matrix()

        # pop our viewport attributes
        glPopAttrib()

        # undo any viewport scissor calls
        pygly.gl.set_scissor(
            pygly.window.create_rectangle( self.window )
            )
        # set our viewport to the entire window
        pygly.gl.set_viewport(
            pygly.window.create_rectangle( self.window )
            )

        # ensure the matrix mode was last set to
        # GL_MODELVIEW
        glMatrixMode( GL_MODELVIEW )


def main():
    # create app
    app = Application()
    app.run()
    app.window.close()


if __name__ == "__main__":
    main()
