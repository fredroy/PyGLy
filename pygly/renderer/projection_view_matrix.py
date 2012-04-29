'''
Created on 20/06/2011

@author: adam
'''

import math

import numpy
from pyglet.gl import *

from view_matrix import ViewMatrix
from pygly.maths import ray
from pygly.maths import matrix44
from pygly.maths import trig


class ProjectionViewMatrix( ViewMatrix ):


    def __init__(
        self,
        aspect_ratio,
        fov = 60.0,
        near_clip = 1.0,
        far_clip = 100.0
        ):
        super( ProjectionViewMatrix, self ).__init__(
            aspect_ratio,
            near_clip,
            far_clip
            )

        self._fov = fov

    def _get_fov( self ):
        return self._fov

    def _set_fov( self, fov ):
        if self._fov == fov:
            return
        self._fov = fov
        self.dirty = True

    fov = property( _get_fov, _set_fov )

    def _update( self ):
        assert self.dirty == True

        # re-calculate the near clip plane
        width, height = self.calculate_near_clip_plane_size()
        width /= 2.0
        height /= 2.0

        # update our frustrum matrix
        self._matrix = matrix44.create_projection_view_matrix(
            -width,
            +width,
            +height,
            -height,
            self.near_clip,
            self.far_clip,
            out = self._matrix
            )
        self.dirty = False

    def calculate_near_clip_plane_size( self ):
        return trig.calculate_plane_size(
            self._aspect_ratio,
            self.fov,
            self.near_clip
            )

    def calculate_far_clip_plane_size( self ):
        return trig.calculate_plane_size(
            self._aspect_ratio,
            self.fov,
            self.far_clip
            )

    def calculate_point_on_plane( self, window, viewport, point, distance ):
        # TODO: remove the need for viewport / window
        # it shouldn't be necessary
        # calculate the near plane's size
        width, height = trig.calculate_plane_size(
            self._aspect_ratio,
            self.fov,
            distance
            )

        # convert the point from a viewport point
        # to a near plane point
        viewport_size = viewport.pixel_rect( window )
        scale = numpy.array(
            [
                width / viewport_size[ (1,0) ],
                height / viewport_size[ (1,1) ]
                ],
            dtype = numpy.float
            )

        # scale the point from viewport coordinates to plane coordinates
        plane_point = numpy.array( point, dtype = numpy.float )
        plane_point *= scale

        # 0,0 is bottom left, we need to make this the centre
        plane_point[ 0 ] -= width / 2.0
        plane_point[ 1 ] -= height / 2.0

        return plane_point

    def point_to_ray( self, window, viewport, point ):
        """
        Returns a local ray cast from the camera co-ordinates
        at 'point'.

        The ray is in intertial space and must be transformed
        to the objects intended translation and orientation.

        @param window: The window the viewport resides on.
        @param viewport: The viewport used for picking.
        @param point: The 2D point, relative to this view matrix,
        to project a ray from. A list of 2 float values.
        [0.0, 0.0] is the Bottom Left.
        [viewport.width, viewport.height] is the Top Right.
        @returns A ray consisting of 2 vectors (shape = 2,3).
        The ray will begin at the near clip plane.
        """
        # calculate the point on the near plane
        near_plane_point = self.calculate_point_on_plane(
            window,
            viewport,
            point,
            self.near_clip
            )
        far_plane_point = self.calculate_point_on_plane(
            window,
            viewport,
            point,
            self.far_clip
            )

        # this point is immediately mappable
        # to a vector from 0,0,0 to
        # point.x, point.y, -near_clip
        near_vec = numpy.array(
            [
                near_plane_point[ 0 ],
                near_plane_point[ 1 ],
                -self.near_clip
                ],
            dtype = numpy.float
            )
        far_vec = numpy.array(
            [
                far_plane_point[ 0 ],
                far_plane_point[ 1 ],
                -self.far_clip
                ],
            dtype = numpy.float
            )

        # convert the 2 vectors into a ray from
        # near_vec to far_vec
        return ray.line_to_ray(
            [
                near_vec,
                far_vec
                ]
            )
