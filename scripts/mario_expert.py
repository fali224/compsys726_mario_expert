"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

from itertools import count
import json
import logging
import random
from telnetlib import theNULL
from typing import Counter
import numpy as np
import time

import cv2
from mario_environment import MarioEnvironment
from pyboy.utils import WindowEvent

count_enemy = 0
forward = 0

class MarioController(MarioEnvironment):
    """
    The MarioController class represents a controller for the Mario game environment.

    You can build upon this class all you want to implement your Mario Expert agent.

    Args:
        act_freq (int): The frequency at which actions are performed. Defaults to 10.
        emulation_speed (int): The speed of the game emulation. Defaults to 0.
        headless (bool): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(
        self,
        act_freq: int = 20,
        emulation_speed: int = 0,
        headless: bool = False,
    ) -> None:
        super().__init__(
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            headless=headless,
        )

        self.act_freq = act_freq

        # Example of valid actions based purely on the buttons you can press
        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
        ]

        self.valid_actions = valid_actions
        self.release_button = release_button

    def run_action(self, action: list) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """
        if action[0] == 0:
            self.pyboy.send_input(self.valid_actions[action[1]])
            for _ in range(5):
                self.pyboy.tick()
            self.pyboy.send_input(self.release_button[action[1]])
        elif action[0] == 1:
            #JUMP
            self.pyboy.send_input(self.valid_actions[2])
            self.pyboy.tick()
            self.pyboy.send_input(self.release_button[2])
            self.pyboy.send_input(self.valid_actions[5])
            self.pyboy.send_input(self.valid_actions[4])
            for _ in range(10):
                self.pyboy.tick()
            self.pyboy.send_input(self.release_button[5])
            self.pyboy.send_input(self.release_button[4])
        # MOVE SLIGHTLY LEFT WHEN BUGGED
        elif action[0] == 2:
            self.pyboy.send_input(self.valid_actions[2])
            self.pyboy.tick()
            self.pyboy.send_input(self.release_button[2])
        # Minor Jump
        elif action[0] == 3:
            self.pyboy.send_input(self.valid_actions[2])
            self.pyboy.tick()
            self.pyboy.send_input(self.release_button[2])
            self.pyboy.send_input(self.valid_actions[5])
            self.pyboy.send_input(self.valid_actions[4])
            for _ in range(3):
                self.pyboy.tick()
            self.pyboy.send_input(self.release_button[5])
            self.pyboy.send_input(self.release_button[4])
        # Simply toggles the buttons being on or off for a duration of act_freq
        #

class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """
    action_1 = [0,2]
    stuck_count = 0
    stuck_count_a = 0
    lock_state = False
    mario_tright = 0
    mario_tleft = 0
    mario_bright = 0
    mario_bleft = 0
    estuck = 0
    is_bigJump = False
    is_jumpStuck = False
    

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path

        self.environment = MarioController(headless=headless)

        self.video = None

    def next_step_ui(self):
        input()
        return

    def choose_action(self):
        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()

        print(game_area)

        count = 0
        body_count = 0
        feet_loc_row = 100
        feet_loc_col = 100


        for i in range(len(game_area)):
            for j in range(len(game_area[i])):
                if game_area[i,j] == 1:
                    body_count = body_count + 1
                    if body_count == 4:
                        feet_loc_row = i
                        feet_loc_col = j
                    elif body_count == 2:
                        feet_loc_row = i
                        feet_loc_col = j   
        if feet_loc_row > 16 or feet_loc_row < 0:
            return [1]
        # Detect inline with legs
        isJumping = True
        if game_area[feet_loc_row + 1 ,feet_loc_col] == 10 or game_area[feet_loc_row + 1 ,feet_loc_col] == 14 or game_area[feet_loc_row + 1 ,feet_loc_col] == 12 or game_area[feet_loc_row + 1 ,feet_loc_col] == 14 or game_area[feet_loc_row + 1 ,feet_loc_col] == 13:
            isJumping = False
        if isJumping:
            return [1]

        priority = []
        for i in range(0,10):
            obstacle_row = 0
            for j in range(len(game_area)):
                if game_area[j,feet_loc_col + i] == 15:  
                    if j < feet_loc_row - 1:
                        if i < 7:
                            priority.append("GOOMBA ABOVE")

                    if j == feet_loc_row or j == feet_loc_row - 1:
                        if i < 5:
                            priority.append("GOOMBA DIRECTLY INFRONT")
                            
                    
                    if j > feet_loc_row:
                        if i < 1:
                            priority.append("GOOMBA BELOW")
                            
                if game_area[j,feet_loc_col + i] == 16:  
                    if j == feet_loc_row or j == feet_loc_row - 1:
                        if i < 5:
                            priority.append("TURTLE DIRECTLY INFRONT")
                
                if game_area[j,feet_loc_col + i] == 18:  
                    if j < feet_loc_row - 1:
                        if i < 7:
                            priority.append("SMASH ABOVE")
                    
                    if j == feet_loc_row or j == feet_loc_row - 1:
                        if i < 5:
                            priority.append("SMASH DIRECTLY INFRONT")
                
                if game_area[j,feet_loc_col + i] == 10 or game_area[j,feet_loc_col + i] == 14:
                    if j <= feet_loc_row:
                        if i < 2:
                            priority.append("OBSTACLE TOO CLOSE")
                        if i < 4:
                            priority.append("OBSTACLE GOOD DISTANCE")
                            
                
                if game_area[j,feet_loc_col + i] == 0:
                    if j == feet_loc_row + 1:
                        if i < 2:
                            priority.append("HOLE")
                            
        if "GOOMBA DIRECTLY INFRONT" in priority or "TURTLE DIRECTLY INFRONT" in priority or "SMASH ABOVE" in priority:
            action_2 = [1]
            return action_2
        elif "GOOMBA ABOVE" in priority or "GOOMBA BELOW" in priority or "SMASH DIRECTLY INFRONT" in priority :
            action_2 = [0,1]
            return action_2
        elif "OBSTACLE TOO CLOSE" in priority:
            action_2 = [0,1]
            return action_2
        elif "OBSTACLE GOOD DISTANCE" in priority:
            action_2 = [1]
            return action_2
        elif "HOLE" in priority:
            action_2 = [1]
            return action_2
                # #Inline with player
                # if j == feet_loc_row or j == feet_loc_row - 1:
                #     if game_area[i,feet_loc_col + i] != 0:
                #         print("OBSTACLE")
                #         action_2 = [1]
                #         return action_2
                
                # # Below player
                # if j > feet_loc_row:
                #     if game_area[j,feet_loc_col+i] == 15:
                #         print("SOMETHING IN THE WAY")
                #         action_2 = [0,1]
                #         return action_2
                #     if game_area[j,feet_loc_col+i] == 0:
                #         print("HOLE")
                #         action_2 = [1]
                #         return action_2
                
                # #Above Player
                # if j < feet_loc_row -1:
                #     if game_area[i,feet_loc_col + i] != 0 and game_area[i,feet_loc_col + i] != 10 and game_area[i,feet_loc_col + i] != 14:
                #         print("SOMETHING IN THE WAY")
                #         action_2 = [0,1]
                #         return action_2

            # distance_to_jump = 4
            # action_1 = [0,4]

            # if game_area[i,feet_loc_col + i] != 0:
            #     j = -1
            #     if game_area[i,feet_loc_col + i] == 16:
            #         distance_to_jump = 5
            #         action_1 = [0,4]
            #     # find where wall ends and if enemy above
            #     if(game_area[feet_loc_row,feet_loc_col + i] == 10 or game_area[feet_loc_row,feet_loc_col + i] == 14):
            #         count = 1
            #         while game_area[feet_loc_row + j,feet_loc_col +i] == game_area[feet_loc_row,feet_loc_col + i]:
            #             j -= 1
            #         # if enemy above then walk backwards
            #         if(game_area[feet_loc_row+ j,feet_loc_col + i] != 0):
            #             action_2 = [1,1]
            #             return action_2
                
            #     if count == 1:
            #         distance_to_jump == 0

            #     if i <= distance_to_jump:
            #         action_2 = action_1
            #         self.action_1 = action_2
            #         return action_2

             
        # for i in range(1,10):
            
        #     if game_area[feet_loc_row-3,feet_loc_col + i] == 18:
        #         action_2 = [1,1]
        #         return action_2


        # # Detect 1 below         
        # for i in range(2,5):
        #     if game_area[feet_loc_row+1,feet_loc_col + i] != 10 and game_area[feet_loc_row+1,feet_loc_col+i] != 14:
        #         if game_area[feet_loc_row+1,feet_loc_col] == 10 or game_area[feet_loc_row+1,feet_loc_col+i] == 14:
        #             print("JUMP")
        #             action_2 = [0,4]
        #             self.action_1 = action_2
        #             return action_2

        
        action_2 = [0,2]
        return action_2





    #     action_1 = self.action_1

    #     is_Gumba = False
    #     is_mon = False
    #     is_mon2 = False
    #     mon_loc_col = 0
    #     mon_loc_row = 0
    #     mon2_loc_col = 0
    #     mon2_loc_row = 0
    #     gum_loc_col = 0
    #     gum_loc_row = 0
    #     is_Stuck = False
    #     print(game_area)

    #     for i in range(len(game_area)):
    #         for j in range(len(game_area[i])):
    #             if game_area[i,j] == 15:
    #                 is_Gumba = True
    #                 gum_loc_col = j
    #                 gum_loc_row = i
    #                 break
    #     for i in range(len(game_area)):
    #         for j in range(len(game_area[i])):
    #             if game_area[i,j] == 16:
    #                 is_mon = True
    #                 mon_loc_col = j
    #                 mon_loc_row = i
    #                 break  
    #     for i in range(len(game_area)):
    #         for j in range(len(game_area[i])):
    #             if game_area[i,j] == 20:
    #                 is_mon2 = True
    #                 mon2_loc_col = j
    #                 mon2_loc_row = i
    #                 break

        


    #     body_count = 0
    #     feet_loc_row = 100
    #     feet_loc_col = 100
    #     for i in range(len(game_area)):
    #         for j in range(len(game_area[i])):
    #             if game_area[i,j] == 1:
    #                 body_count = body_count + 1
    #                 if body_count == 4:
    #                     feet_loc_row = i
    #                     feet_loc_col = j
    #                 elif body_count == 2:
    #                     feet_loc_row = i
    #                     feet_loc_col = j

    #     # print(feet_loc_col)
    #     # print(feet_loc_row)

    #     if body_count == 4:
    #         self.mario_bleft = [feet_loc_row, feet_loc_col - 1]
    #         self.mario_bright = [feet_loc_row, feet_loc_col]
    #         self.mario_tleft = [feet_loc_row - 1, feet_loc_col]
    #         self.mario_tright = [feet_loc_row - 1, feet_loc_col - 1]

    #     #if action_1 == [0,4] and missing logic
    #     if game_area[14, 10] == 0 and game_area[15,10] == 10:
    #         action_2 = [0,2]
    #         self.action_1 = action_2
    #         return action_2
        
    #     if self.estuck > 4:
    #         action_2 = [0,1]
    #         self.action_1 = action_2
    #         self.estuck = 0
    #         return action_2
        
    #     if self.lock_state == True:
    #         action_2 = [1,4]
    #         self.action_1 = action_2
    #         self.is_bigJump = True
    #         return action_2
    #     #no jumpstuck logic
    #     #no above head block
    #     #missig logic
    #     if self.stuck_count < 2 and self.stuck_count_a < 150:
    #         if game_area[feet_loc_row, feet_loc_col+1] == 10:
    #             print('mon4')
    #             action_2 = [0,4]
    #             if self.action_1 == action_2:
    #                 self.stuck_count = self.stuck_count + 1
    #             self.action_1 = action_2
    #             return action_2

    #         elif (is_Gumba == True and gum_loc_col - feet_loc_col <= 1):
    #             # if not self.action_1 == [0,4]:
    #             #     action_2 = [0,1]
    #             #     self.action_1 = action_2
    #             #     return action_2
    #             action_2 = [0,4]
    #             if self.action_1 == action_2:
    #                 self.stuck_count = self.stuck_count + 1
    #             self.action_1 = action_2
    #             self.stuck_count = 0
    #             return action_2
    # #missing logic
    #         elif (is_mon == True and mon_loc_col - feet_loc_col <= 30):
    #             print('mon')
    #             action_2 = [0,4]
    #             if self.action_1 == action_2:
    #                 self.stuck_count = self.stuck_count + 1
    #             self.action_1 = action_2
    #             self.stuck_count = 0
    #             return action_2

    #         elif (is_mon2 == True and mon2_loc_col - feet_loc_col <= 30):
    #             print('mon1')
    #             action_2 = [0,4]
    #             if self.action_1 == action_2:
    #                 self.stuck_count = self.stuck_count + 1
    #             self.action_1 = action_2
    #             self.stuck_count = 0 
    #             return action_2

    #         elif game_area[14,10] == 0:
    #             if game_area[14,12] == 0:
    #                 action_2 = [1,4]
    #                 self.action_1 = action_2
    #                 return action_2
    #             print('mon2')
    #             action_2 = [0,4]
    #             if self.action_1 == action_2:
    #                 self.stuck_count = self.stuck_count + 1
    #             self.action_1 = action_2
    #             self.stuck_count = 0
    #             return action_2
            
    #         else:
    #             action_2 = [0,2]
    #             if self.action_1 == action_2:
    #                 self.stuck_count_a = self.stuck_count_a + 1
    #             self.action_1 = action_2
    #             self.stuck_count = 0
    #             return action_2
            
    #     elif self.stuck_count_a == 150:
    #         print('mon3')
    #         action_2 = [0,4]
    #         self.action_1 = action_2
    #         self.stuck_count_a = 0
    #         return action_2
        
    #     else:
    #         action_2 = [0,1]
    #         self.action_1 = action_2
    #         self.stuck_count = 0
    #         self.stuck_count_a = 0
    #         return action_2
        









        






        # global count_enemy
        # count_enemy = 0
        # global forward
        # forward = 0

        # enemy_process = self.environment._read_m(0xFFFB)
        # mario_pos = self.environment._read_m(0xC202)

        # if mario_pos > 75:
        #     print(game_area)
        #     if (enemy_process == count_enemy):
        #         enemy_loc = 0xD100 + (count_enemy * 0x10) + 3 
        #         enemy = self.environment._read_m(enemy_loc)
        #         count_enemy = count_enemy + 1

        #         #print(enemy)
        #         #print(enemy - mario_pos)
        #         if (enemy - mario_pos <= 40):
        #             return (4)
        #         elif(forward > 3):
        #             forward = 0
        #             return (4)
        #         else:
        #             forward = forward + 1

        # Implement your code here to choose the best action
        # time.sleep(0.1)
        #return(2)
        #return random.randint(0, len(self.environment.valid_actions) - 1)

    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Choose an action - button press or other...
        action = self.choose_action()

        # Run the action on the environment
        self.environment.run_action(action)

    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(f"{self.results_path}/mario_expert.mp4", width, height)

        while not self.environment.get_game_over():
            frame = self.environment.grab_frame()
            self.video.write(frame)

            self.step()

        final_stats = self.environment.game_state()
        logging.info(f"Final Stats: {final_stats}")

        with open(f"{self.results_path}/results.json", "w", encoding="utf-8") as file:
            json.dump(final_stats, file)

        self.stop_video()

    def start_video(self, video_name, width, height, fps=30):
        """
        Do NOT edit this method.
        """
        self.video = cv2.VideoWriter(
            video_name, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

    def stop_video(self) -> None:
        """
        Do NOT edit this method.
        """
        self.video.release()
