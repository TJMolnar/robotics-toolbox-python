# PoERobot
import numpy as np
from spatialmath import Twist3, SE3
from spatialmath.base import skew
from roboticstoolbox.robot import Link, Robot


class PoELink(Link):
    """
    Product of exponential link class

    This is a subclass of the base Link class.

    :seealso: :class:`Link`
    """

    def __str__(self):
        return super().__str__() + ", S = " + str(self.S)

class PoERevolute(PoELink):

    def __init__(self, axis, point, **kwargs):
        """
        Construct revolute product of exponential link

        :param axis: axis of rotation
        :type axis: array_like(3)
        :param point: point on axis of rotation
        :type point: array_like(3)

        Construct a link and revolute joint for a PoE Robot.

        :seealso: :class:`Link` :class:`Robot`
        """

        super().__init__(**kwargs)
        self.S = Twist3.UnitRevolute(axis, point)

class PoEPrismatic(PoELink):


    def __init__(self, axis, **kwargs):
        """
        Construct prismatic product of exponential link

        :param axis: direction of motion
        :type axis: array_like(3)

        Construct a link and prismatic joint for a PoE Robot.

        :seealso: :class:`Link` :class:`Robot`
        """
        super().__init__(**kwargs)
        self.S = Twist3.UnitPrismatic(axis)

class PoERobot(Robot):

    def __init__(self, links, T0, **kwargs):
        """
        Product of exponential robot class

        :param links: robot links
        :type links: list of ``PoELink``
        :param T0: end effector pose for zero joint coordinates
        :type T0: SE3

        This is a subclass of the abstract base Robot class that provides
        only forward kinematics and world-frame Jacobian.

        :seealso: :class:`PoEPrismatic` :class:`PoERevolute`
        """

        self._n = len(links)

        super().__init__(links, **kwargs)
        self.T0 = T0


    def __str__(self):
        """
        Pretty prints the PoE Model of the robot.
        :return: Pretty print of the robot model
        :rtype: str
        """
        s = ""
        for j, link in enumerate(self):
            s += f"{j}: {link.S}\n"

        s += f"T0: {self.T0.strline()}"
        return s

    def nbranches(self):
        return 0

    def fkine(self, q):
        """
        Forward kinematics

        :param q: joint configuration
        :type q: array_like(n)
        :return: end effector pose
        :rtype: SE3
        """
        T = None
        for link, qk in zip(self, q):
            if T is None:
                T = link.S.exp(qk)
            else:
                T *= link.S.exp(qk)

        return T * T0

        # T = reduce(lambda x, y: x * y,
        #           [link.A(qk) for link, qk in zip(self, q)])

    def jacob0(self, q):
        """
        Jacobian in world frame

        :param q: joint configuration
        :type q: array_like(n)
        :return: Jacobian matrix
        :rtype: ndarray(6,n)
        """
        columns = []
        T = SE3()
        for link, qk in zip(self, q):
            columns.append(T.Ad() @ link.S.S)
            T *= link.S.exp(qk)
        T *= self.T0
        J = np.column_stack(columns)

        # convert Jacobian from velocity twist to spatial velocity
        Jsv = np.eye(6)
        Jsv[:3, 3:] = -skew(T.t)
        return Jsv @ J

    def jacobe(self, q):
        """
        Jacobian in end-effector frame

        :param q: joint configuration
        :type q: array_like(n)
        :return: Jacobian matrix
        :rtype: ndarray(6,n)
        """
        columns = []
        T = SE3()
        for link, qk in zip(self, q):
            columns.append(T.Ad() @ link.S.S)
            T *= link.S.exp(qk)
        T *= self.T0
        J = np.column_stack(columns)

        # convert velocity twist from world frame to EE frame
        return T.inv().Ad() @ J


if __name__ == "__main__":  # pragma nocover

    T0 = SE3.Trans(2, 0, 0)

    # rotate about z-axis, through (0,0,0)
    link1 = PoERevolute([0, 0, 1], [0, 0, 0], name='foo')
    # rotate about z-axis, through (1,0,0)
    link2 = PoERevolute([0, 0, 1], [1, 0, 0])
    # end-effector pose when q=[0,0]
    TE0 = SE3.Trans(2, 0, 0)

    print(link1)
    robot = PoERobot([link1, link2], T0)

    q = [0, np.pi/2]
    # q = [0, 0]

    robot.fkine(q).printline()
    print(robot.jacob0(q))
    print(robot.jacobe(q))
    print(robot)
