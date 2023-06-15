''' This code has been adapted from:
***************************************************************************************
*    Title: "Biologically inspired spatial navigation using vector-based and topology-based path planning"
*    Author: "Tim Engelmann"
*    Date: 28.09.2021
*    Code version: 1.0
*    Availability: https://drive.google.com/file/d/1g7I-n9KVVulybh1YeElSC-fvm9_XDoez/view
*
***************************************************************************************
'''
''' Egocentric Ray Detection from:
***************************************************************************************
*    Title: "Biologically Plausible Spatial Navigation Based on Border Cells"
*    Author: "Camillo Heye"
*    Date: 28.08.2021
*    Availability: https://drive.google.com/file/d/1RvmLd5Ee8wzNFMbqK-7jG427M8KlG4R0/view
*
***************************************************************************************
'''
''' Camera and Object Loading from:
***************************************************************************************
*    Title: "Simulate Images for ML in PyBullet — The Quick & Easy Way"
*    Author: "Mason McGough"
*    Date: 19.08.2019
*    Availability: https://towardsdatascience.com/simulate-images-for-ml-in-pybullet-the-quick-easy-way-859035b2c9dd
*
***************************************************************************************
'''
''' Keyboard Movement from:
***************************************************************************************
*    Title: "pyBulletIntro"
*    Author: "Ramin Assadollahi"
*    Date: 16.05.2021
*    Availability: https://github.com/assadollahi/pyBulletIntro
*
***************************************************************************************
'''
import pybullet as p
import time
import os
import sys
import pybullet_data
import numpy as np
import math

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))
import system.plotting.plotResults as plot
from system.controller.local_controller.local_navigation import compute_navigation_goal_vector

class PybulletEnvironment:
    """This class deals with everything pybullet or environment (obstacles) related"""
    def __init__(self, visualize,dt,env_model,mode,buildDataSet=False,start=None,orientation=False):
        """ Create environment.
        
        arguments:
        visualize   -- opens JAVA application to see agent in environment
        dt          -- timestep for simulation
        env_model   -- layout of obstacles in the environment 
                    (choices: "plane", "Savinov_val2", "Savinov_val3", "Savinov_test7")
        mode        -- choose goal vector calculation (choices: "analytical", "keyboard", "pod", "linear_lookahead")
        buildDataSet-- camera images are only taken when this is true
        start       -- the agent's [x,y] starting position (default [0,0])
        orientation -- the agent's starting orientation (default np.pi/2 (faces North))
        """
        
        try:
            p.disconnect() 
        except:
            pass

        self.visualize = visualize  # to open JAVA application

        if self.visualize:
            p.connect(p.GUI)
            
            if mode == "keyboard":
                p.setRealTimeSimulation(1)
        else:
            p.connect(p.DIRECT)

        self.env_model = env_model
        self.arena_size = 15

        base_position = [0, 0.05, 0.02]  # [0, 0.05, 0.02] ensures that it actually starts at origin

        # environment choices       
        if env_model == "Savinov_val3":
            base_position = [-2, 0.05, 0.02]
            p.resetDebugVisualizerCamera(cameraDistance=10, cameraYaw=0, cameraPitch=-70, cameraTargetPosition=[-2, -0.35, 5.0])
            #p.resetDebugVisualizerCamera(cameraDistance=1.5, cameraYaw=0, cameraPitch=-70, cameraTargetPosition=[-0.55, -0.35, 5.0])
            self.dimensions = [-9, 6, -5, 4]
        elif env_model == "Savinov_val2":
            base_position = [0, 3.05, 0.02]
            p.resetDebugVisualizerCamera(cameraDistance=10, cameraYaw=0, cameraPitch=-70, cameraTargetPosition=[0.55, -0.35, 5.0])
            self.dimensions = [-5, 5, -5, 5]
        elif env_model == "Savinov_test7":
            base_position = [-1, 0.05, 0.02]
            p.resetDebugVisualizerCamera(cameraDistance=10, cameraYaw=0, cameraPitch=-70, cameraTargetPosition=[-1.55, -0.35, 5.0])
            self.dimensions = [-9, 6, -4, 4]
        elif env_model == "plane":
            p.resetDebugVisualizerCamera(cameraDistance=4.5, cameraYaw=0, cameraPitch=-70, cameraTargetPosition=[0,0,0])
            urdfRootPath = pybullet_data.getDataPath()
            p.loadURDF(os.path.join(urdfRootPath, "plane.urdf"))
        elif "obstacle" in env_model:
            dirname = os.path.dirname(__file__)
            plane = os.path.realpath(os.path.join(dirname, "environment/"+self.env_model+"/plane.urdf"))
            p.loadURDF(plane)
        else:
            raise ValueError("No matching env_model found.")
        
        if "Savinov" in env_model:
            #load the plane and maze with desired textures
            self.mazeID = self.__load_obj("mesh.obj","yellow_wall.png")
            self.planeID = self.__load_obj("plane100.obj","green_floor.png")

        p.setGravity(0, 0, -9.81)

        self.dt = dt
        p.setTimeStep(self.dt)  
        
        #starting position and orientation of the agent
        if start:
            base_position = [start[0],start[1],0.02] 
        if orientation:
            orientation = p.getQuaternionFromEuler([0,0,orientation]) 
        else:
            orientation = p.getQuaternionFromEuler([0, 0, np.pi/2])  # faces North

        max_speed = 5.5  # determines speed at which agent travels: max_speed = 5.5 -> actual speed of ~0.5 m/s             

        #load agent
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, "p3dx/urdf/pioneer3dx.urdf")
        self.carID = p.loadURDF(filename, basePosition=base_position, baseOrientation=orientation)  
        #check if agent touches maze -> invalid start position
        if not env_model == "plane" and not "obstacle" in env_model and self.detect_maze_agent_contact():
            raise ValueError("Invalid start position. Agent and maze overlap.") 

        
        self.goal_vector_original = np.array([1, 1])  # egocentric goal vector after last recalculation
        self.goal_vector = np.array([0, 0])  # egocentric goal vector after last update
        self.goal_pos =  None # used for analytical goal vector calculation and plotting

        self.xy_coordinates = []  # keeps track of agent's coordinates at each time step
        self.orientation_angle = []  # keeps track of agent's orientation at each time step
        self.xy_speeds = []  # keeps track of agent's speed (vector) at each time step
        self.nr_ofsteps = 0 #keeps track of number of steps taken with current decoder (used for switching between pod and linlook decoder)
        self.speeds = []  # keeps track of agent's speed (value) at each time step
        self.goal_vector_array = [] # keeps track of agent's goal vector at each time step
        self.save_position_and_speed()  # save initial configuration
        
        
        self.buildDataSet = buildDataSet # when true create camera images
        self.images = [] # if buildDataSet: collect images

        self.max_speed = max_speed
        
        self.mode = mode # choose navigation mode, different decoders have different thresholds for e.g. arrival
        
        self.buffer = 0 # buffer for checking if agent got stuck, discards timesteps spent turning towards the goal
        
        # egocentric beams checking for object collision
        self.num_ray_dir = 21 # number of direction to check for obstacles
        self.tactile_cone = 120 # cone for beams centered on heading direction
        self.ray_length = 1 # length of the beams
        self.mapping = None # see local_navigation experiments
        self.combine = None
        
        # threshold for goal_vector length that signals arrival at goal
        self.pod_arrival_threshold = 0.5
        self.lin_look_arrival_threshold = 0.2
        self.analytical_arrival_threshold = 0.15

    def __load_obj(self, objectFilename, textureFilename):
        """load object files with specified texture into the environment"""
        dirname = os.path.dirname(__file__)
        object = os.path.realpath(os.path.join(dirname, "environment/"+self.env_model+"/"+objectFilename))
        texture = os.path.realpath(os.path.join(dirname, "environment/textures/"+textureFilename))

        visualShapeId = p.createVisualShape(
            shapeType = p.GEOM_MESH,
            fileName = object,
            rgbaColor = None,
            meshScale = [1,1,1])
        
        collisionShapeId = p.createCollisionShape(
            shapeType = p.GEOM_MESH,
            fileName = object,
            meshScale = [1,1,1])
        
        multiBodyId = p.createMultiBody(
            baseMass = 0.0,
            baseCollisionShapeIndex = collisionShapeId,
            baseVisualShapeIndex=visualShapeId,
            basePosition=[0, 0, 0],
            baseOrientation=p.getQuaternionFromEuler([0, 0, 0]))
        
        textureId = p.loadTexture(texture)
        p.changeVisualShape(multiBodyId, -1, textureUniqueId = textureId)
        return multiBodyId

    def camera(self,agent_pos_orn = None):
        """ simulates a camera mounted on the robot, creating images """
        if not self.buildDataSet and not self.visualize:
            return
        
        distance = 100000
        img_w, img_h = 64, 64
        
        if agent_pos_orn:
            agent_pos, agent_orn = agent_pos_orn
            agent_pos = (agent_pos[0],agent_pos[1],0.02)
            yaw = agent_orn
        else: 
            agent_pos, agent_orn =\
                p.getBasePositionAndOrientation(self.carID)

            yaw = p.getEulerFromQuaternion(agent_orn)[-1]
            
        xA, yA, zA = agent_pos
        zA = zA + 0.3 # make the camera a little higher than the robot
        
        #Put the camera in front of the robot to simulate eyes
        xA = xA + math.cos(yaw) * 0.2
        yA = yA + math.sin(yaw) * 0.2

        # compute focusing point of the camera
        xB = xA + math.cos(yaw) * distance
        yB = yA + math.sin(yaw) * distance
        zB = zA
    
        view_matrix = p.computeViewMatrix(
                        cameraEyePosition=[xA, yA, zA],
                        cameraTargetPosition=[xB, yB, zB],
                        cameraUpVector=[0, 0, 1.0]
                    )

        projection_matrix = p.computeProjectionMatrixFOV(
                                fov=120, aspect=1.5, nearVal=0.02, farVal=3.5)
        
        img = p.getCameraImage(img_w, img_h,
                                view_matrix,
                                projection_matrix, shadow=True,
                                renderer=p.ER_BULLET_HARDWARE_OPENGL)
        
        if self.buildDataSet:
            self.images.append(img)
        
        return img
    
    def __keyboard_movement(self):
        """ simulates a timestep with keyboard controlled movement """
        keys = p.getKeyboardEvents()
        for k,v in keys.items():

                if (k == p.B3G_RIGHT_ARROW and (v&p.KEY_WAS_TRIGGERED)):
                        self.turn = -0.5
                if (k == p.B3G_RIGHT_ARROW and (v&p.KEY_WAS_RELEASED)):
                        self.turn = 0
                if (k == p.B3G_LEFT_ARROW and (v&p.KEY_WAS_TRIGGERED)):
                        self.turn = 0.5
                if (k == p.B3G_LEFT_ARROW and (v&p.KEY_WAS_RELEASED)):
                        self.turn = 0

                if (k == p.B3G_UP_ARROW and (v&p.KEY_WAS_TRIGGERED)):
                        self.forward=1
                if (k == p.B3G_UP_ARROW and (v&p.KEY_WAS_RELEASED)):
                        self.forward=0
                if (k == p.B3G_DOWN_ARROW and (v&p.KEY_WAS_TRIGGERED)):
                        self.forward=-1
                if (k == p.B3G_DOWN_ARROW and (v&p.KEY_WAS_RELEASED)):
                        self.forward=0
                if (k == p.B3G_SPACE and (v&p.KEY_WAS_TRIGGERED)):                    
                        return False
           
        v_left = (self.forward-self.turn)*self.max_speed
        v_right = (self.forward+self.turn)*self.max_speed
        gains = [v_left,v_right]
        self.change_speed(gains)
        p.stepSimulation()
        self.save_position_and_speed()
        if self.visualize:
            time.sleep(self.dt/5)
        self.camera()
        return True

    def keyboard_simulation(self):
        """ Control the agent with your keyboard. SPACE ends the simulation."""
        self.forward = 0
        self.turn = 0
        flag = True
        while flag:
            flag = self.__keyboard_movement()
    
    def detect_maze_agent_contact(self):
        """ true, if the robot is in contact with the maze """
        return bool(p.getContactPoints(self.carID, self.mazeID))
    
    def compute_movement(self,goal_vector):
        """Compute and set motor gains of agents. Simulate the movement with py-bullet"""
        
        gains = self.compute_gains(goal_vector)

        self.change_speed(gains)
        p.stepSimulation()

        self.save_position_and_speed()
        if self.visualize:
            time.sleep(self.dt/5)
     
    def navigation_step(self,gc = None,pod = None,obstacles = True):
        """ One navigation step for the agent. 
            Calculate or update the goal vector.
            Calculate obstacle vector.
            Combine into movement vector and simulate movement.
        
        arguments:
        gc          -- grid cell network for path integration and goal vector calculation 
        pod         -- phase offset decode network for goal vector calculation
        obstacles   -- if true use obstacle avoidance
        """
        if self.mode == "analytical":
            self.goal_vector = self.calculate_goal_vector_analytically()
        else:
            self.goal_vector = self.calculate_goal_vector_gc(gc,pod)

        if obstacles: 
            obstacle_vector = self.calculate_obstacle_vector()
            
            if np.linalg.norm(np.array(obstacle_vector))>0:
                obstacle_vector = np.array(obstacle_vector)/(np.linalg.norm(np.array(obstacle_vector)))#normalize obstacle_vector to a standard length of 1
            else:
                obstacle_vector= np.array([0.0,0.0])
            
            if np.linalg.norm(np.array(self.goal_vector))>0:
                normed_goal_vector = np.array(self.goal_vector)/np.linalg.norm(np.array(self.goal_vector))#normalize goal_vector to a standard length of 1
            else:
                normed_goal_vector= np.array([0.0,0.0])
            
            #combine goal and obstacle vector
            if self.combine:
                movement = list(normed_goal_vector*self.combine + obstacle_vector*-1)
            else:
                movement = list(normed_goal_vector*1.5 + obstacle_vector*-1)
        else:
            movement = self.goal_vector
        self.compute_movement(movement)
        
        # grid cell network track movement
        if gc:
            xy_speed = self.xy_speeds[-1]
            gc.track_movement(xy_speed)
        self.camera()
    
    def compute_angle(self,vec_1, vec_2):
        length_vector_1 = np.linalg.norm(vec_1)
        length_vector_2 = np.linalg.norm(vec_2)
        if length_vector_1 == 0 or length_vector_2 == 0:
            return 0
        unit_vector_1 = vec_1 / length_vector_1
        unit_vector_2 = vec_2 / length_vector_2
        dot_product = np.dot(unit_vector_1, unit_vector_2)
        angle = np.arccos(dot_product)
    
        vec = np.cross([vec_1[0], vec_1[1], 0], [vec_2[0], vec_2[1], 0])
    
        return angle * np.sign(vec[2])

    def compute_gains(self,goal_vector):
        ''' computes the motor gains resulting from (inhibited) goal vector'''
        current_angle = self.orientation_angle[-1]
        current_heading = [np.cos(current_angle), np.sin(current_angle)]
        diff_angle = self.compute_angle(current_heading, goal_vector) / np.pi
        
        #threshold for turning: turning too sharply is not biologically accurate
        if abs(diff_angle) > math.radians(30/math.pi): 
            diff_angle = math.copysign(math.radians(30/math.pi), diff_angle)
       
        gain = min(np.linalg.norm(goal_vector) * 5, 1)

        # If close to the goal do not move
        if gain < 0.5:
            gain = 0

        # For biologically inspired movement: only adjust course slightly
        # TODO: Future Work: This restricts robot movement too severely
        max_speed = self.max_speed
        v_left = max_speed * (1 - diff_angle * 2) * gain
        v_right = max_speed * (1 + diff_angle * 2) * gain
        
        return [v_left, v_right]
     
    def change_speed(self, gains):
        p.setJointMotorControlArray(bodyUniqueId=self.carID,
                                    jointIndices=[4, 6],
                                    controlMode=p.VELOCITY_CONTROL,
                                    targetVelocities=gains,
                                    forces=[10, 10])

    def save_position_and_speed(self):
        [position, angle] = p.getBasePositionAndOrientation(self.carID)
        angle = p.getEulerFromQuaternion(angle)
        self.xy_coordinates.append(np.array([position[0], position[1]]))
        self.orientation_angle.append(angle[2])

        [linear_v, _] = p.getBaseVelocity(self.carID)
        self.xy_speeds.append([linear_v[0], linear_v[1]])
        self.speeds.append(np.linalg.norm([linear_v[0], linear_v[1]]))
        self.goal_vector_array.append(self.goal_vector)
        self.nr_ofsteps += 1

    def end_simulation(self):
        p.disconnect()
       
    def add_debug_line(self,start,end,color,width=1):
        """ add line into visualization """
        if self.visualize:
            p.addUserDebugLine(start,end,color,width)
         
    def ray_detection_egocentric(self):
        """ returns the egocentric distance to obstacles in numRays directions """
        
        if self.visualize: p.removeAllUserDebugItems() #removes raylines
        
        rayReturn = []
        rayFrom = []
        rayTo = []
        numRays = self.num_ray_dir    #number of directions to check (e.g. 16,51,71)
        rayLen = self.ray_length      #length of the rays
        rayHitColor = [1, 0, 0]
        rayMissColor = [1, 1, 1]
        
        
        ray_angles = []

        for i in range(numRays):
            rayFromPoint = p.getLinkState(self.carID, 0)[0] #linkWorldPosition
            rayReference = p.getLinkState(self.carID, 0)[1] #linkWorldOrientation
            euler_angle = p.getEulerFromQuaternion(rayReference)  # in degree

            rayFromPoint = list(rayFromPoint)
            rayFromPoint[2] = rayFromPoint[2] + 0.02 #see p3dx model
            rayFrom.append(rayFromPoint)
            
            #1 pi rotation -> 180 degrees
            sub = euler_angle[2] - 2 * math.pi * i/(numRays-1) * self.tactile_cone/360+ math.pi/(360.0/self.tactile_cone)
            
            rayTo.append([
                rayLen * math.cos( sub
                    ) +
                rayFromPoint[0],
                rayLen * math.sin( sub
                    ) +
                rayFromPoint[1],
                rayFromPoint[2]
            ])
            
            ray_angles.append(sub)
        
        
        results = p.rayTestBatch(rayFrom, rayTo, numThreads=0)  #get intersections with obstacles
        for i in range(numRays):
            hitObjectUid = results[i][0]

            if (hitObjectUid < 0):
                hitPosition = [0, 0, 0]
                self.add_debug_line(rayFrom[i], rayTo[i], rayMissColor)
                if(i ==0):
                    self.add_debug_line(rayFrom[i], rayTo[i], (0,0,0))
                self.add_debug_line(rayFrom[i], rayTo[i], rayMissColor)
                rayReturn.append(-1)
            else:
                hitPosition = results[i][3]
                self.add_debug_line(rayFrom[i], hitPosition, rayHitColor)
                self.add_debug_line(rayFrom[i], rayTo[i], rayHitColor)
                rayReturn.append(
                    math.sqrt((hitPosition[0] - rayFrom[i][0]) ** 2 + (hitPosition[1] - rayFrom[i][1]) ** 2))

        return rayReturn,ray_angles
    
    ''' Calculates the obstacle_vector from the ray distances'''
    def calculate_obstacle_vector(self):
        
        rays,angles = self.ray_detection_egocentric()
        
        '''different choices for mapping ray distance to motor inhibition'''
        if self.mapping:
            m = lambda d: self.mapping/(d+0.0001)
        else:
            m = lambda d: 1.5/(d+0.0001)
        
        rays = list(map(lambda d: 0 if d < 0 else m(d) ,rays))
        
        obstacle_vector = np.array([0.0,0.0])
        seperate = []
        for i,r in enumerate(rays):
            seperate.append(np.array([
                np.cos(angles[i]),
                np.sin(angles[i])]) * r)
        
        obstacle_vector = sum(seperate)
        
        return np.array(obstacle_vector)
            
    def calculate_goal_vector_analytically(self):
        """ Uses a precise goal vector. """
        rayFromPoint = p.getLinkState(self.carID, 0)[0] #linkWorldPosition
        goal_vector = [-rayFromPoint[0] + self.goal_pos[0],-rayFromPoint[1] + self.goal_pos[1]]

        return goal_vector
    
    def calculate_goal_vector_gc(self,gc_network,pod_network):
        """ Uses decoded grid cell spikings as a goal vector. """
        ret = compute_navigation_goal_vector(gc_network,self.nr_ofsteps, self,model=self.mode,pod=pod_network)            
        return ret
    
    def run_over(self):
        ''' Returns robot status during navigation
        
        returns:
        0   -- robot still moving
        1   -- robot arrived at goal
        -1  -- robot stuck
        '''


        if self.mode == "pod" and abs(np.linalg.norm(self.goal_vector))<self.pod_arrival_threshold:
            return 1
        
        if self.mode == "linear_lookahead" and abs(np.linalg.norm(self.goal_vector))<self.lin_look_arrival_threshold:
            return 1
        
        if self.mode == "analytical" and abs(np.linalg.norm(self.calculate_goal_vector_analytically()))<self.analytical_arrival_threshold:
            return 1
        
        # threshold for considering the agent as stuck
        if self.mode == "analytical":
            stop = 100
        else:
            stop = 200

        if self.buffer + stop < len(self.xy_coordinates) and stop < len(self.xy_coordinates):
            if np.linalg.norm(self.xy_coordinates[-1]-self.xy_coordinates[-stop])<0.1:
                return -1
        
        #Still going
        return 0
    
    def turn_to_goal(self,gc_network=None,pod_network=None):
        """ Agent turns to face in goal vector direction """
        if self.mode == "analytical":
            self.goal_vector = self.calculate_goal_vector_analytically()
        elif pod_network: 
            self.goal_vector = self.calculate_goal_vector_gc(gc_network,pod_network) #recalculate goal_vector
            
        
        if np.linalg.norm(np.array(self.goal_vector))==0: return
        
        i=0
        while i==0 or (abs(diff_angle) > 0.05 and i<5000):
            i+=1
            normed_goal_vector = np.array(self.goal_vector)/np.linalg.norm(np.array(self.goal_vector))
            
            current_angle = self.orientation_angle[-1]
            current_heading = [np.cos(current_angle), np.sin(current_angle)]
            diff_angle = self.compute_angle(current_heading, normed_goal_vector) / np.pi
            
            gain = min(np.linalg.norm(normed_goal_vector) * 5, 1)
    
            # If close to the goal do not move
            if gain < 0.5:
                gain = 0
                
            # If large difference in heading, do an actual turn
            if abs(diff_angle) > 0.05 and gain > 0:
                max_speed = self.max_speed / 2
                direction = np.sign(diff_angle)
                if direction > 0:
                    v_left = max_speed * gain * -1
                    v_right = max_speed * gain
                else:
                    v_left = max_speed * gain
                    v_right = max_speed * gain * -1
            else:
                v_left = 0
                v_right = 0
            
            gains = [v_left,v_right]
    
            self.change_speed(gains)
            p.stepSimulation()
    
            self.save_position_and_speed()
            if self.visualize:
                time.sleep(self.dt/5)
        
        #turning in place does not mean the agent is stuck       
        self.buffer = len(self.xy_coordinates)

if __name__ == "__main__":
    print("Test keyboard movement an plotting in different environments. Press SPACE to exit.")
    """
    Available environments:
    - plane: just a plane
    - Savinov_test7
    - Savinov_val2
    - Savinov_val3
    """
    env_model = "plane" 
    env_model = "obstacle_map_1"
    env_model = "Savinov_test7"
    env_model = "Savinov_val2"
    env_model = "Savinov_val3"

    dt = 1e-2
    env = PybulletEnvironment(True,dt,env_model,mode = "keyboard")
    env.keyboard_simulation()

    # plot the agent's trajectory in the environment
    plot.plotTrajectoryInEnvironment(env)

    env.end_simulation()
