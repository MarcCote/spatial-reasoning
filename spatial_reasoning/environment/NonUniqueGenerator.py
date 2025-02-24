import math, random, pdb
import numpy as np
from spatial_reasoning.environment import library
from collections import defaultdict
from spatial_reasoning.environment.reference_instructions import create_references

'''
global: northernmost, southernmost, etc
proximity: < nonunique > closest to < unique >
relational: < nonunique > in between the < unique > and < unique >
N to the < direction > of < unique > and N' to the < direction > of < unique >
'''

class NonUniqueGenerator:

    def __init__(self, objects, unique_instructions, shape = (20,20), goal_value = 3, num_steps = 50, only_global = False):
        self.objects = objects
        self.unique_instructions = unique_instructions
        self.shape = shape
        self.goal_value = goal_value
        self.num_steps = num_steps
        self.only_global = only_global

    def __all_positions(self, unique, nonunique):
        positions = []
        positions.extend( unique.values() )
        for name, pos in nonunique.items():
                positions.extend( pos )
        # print(positions)
        return positions

    def __remove_positions(self, whole, part):
        if type(part[0]) == list:
            for p in part:
                whole.remove(p)
        elif type(part[0]) == int:
            whole.remove(part)
        else:
            raise RuntimeError('Unexpected part type: ', type(part), part)
        return whole

    def __valid_position(self, world, pos):
        grass_ind = library.objects['grass']['index']
        # pos = tuple(map(sum, zip(pos, ref)))
        if pos[0] < 0 or pos[0] >= world.shape[0]:
            return False
        if pos[1] < 0 or pos[1] >= world.shape[1]:
            return False

        if world[pos] == grass_ind:
            return True
        else:
            return False
        # pdb.set_trace()

    def __place(self, world, pos, ind):
        grass_ind = library.objects['grass']['index']
        if world[pos] != grass_ind:
            print(world)
            raise RuntimeError('Placing ', ind, ' in non-grass pos: ', pos)
        world[pos] = ind
        return world

    def new(self):
        directions = {}
        world = self.__puddles(self.num_steps)

        valid_states = [(i,j) for i in range(world.shape[0]) \
                        for j in range(world.shape[1]) \
                        if world[i][j] != self.objects['puddle']['index'] ]

        unique_indices = [(i[0], i[1]['index']) for i in self.objects.items() if not i[1]['background'] and i[1]['unique']]
        nonunique_indices = [(i[0], i[1]['index']) for i in self.objects.items() if not i[1]['background'] and not i[1]['unique']]
        used_unique = []

        unique_positions = {}
        nonunique_positions = defaultdict(lambda: [])

        reference_probability = 0.75
        nonunique_reference_probability = 0.75
        grass_ind = library.objects['grass']['index']
        ## add unique objects
        for name, obj in self.objects.items():

            if not obj['background'] and obj['unique']:
                ind = obj['index']

                if ind in used_unique:
                    continue

                assert( ind not in used_unique )
                used_unique.append(ind)

                pos = random.choice(valid_states)
                # print('UNIQUE: ', name, pos)
                while world[pos] != grass_ind: # in self.__all_positions(unique_positions, nonunique_positions): # unique_positions.values():
                    pos = random.choice(valid_states)

                world = self.__place(world, pos, ind)

                '''
                N above and N' to the right of < unique >
                '''
                unique_positions[name] = pos
                if not self.only_global:
                    object_specific_directions = self.unique_directions(world, pos, name)
                    for (instr, goal) in object_specific_directions:
                        directions[instr] = goal
                # directions[name] = object_specific_dir

                '''
                < nonunique > N above < unique > and N' to the right of < unique >
                '''
                ## add new unique object to reference
                if np.random.rand() < reference_probability and len(used_unique) < len(unique_indices):
                    ## choose reference object
                    unique2_name, unique2_ind = random.choice(unique_indices)
                    while unique2_ind in used_unique:
                        unique2_name, unique2_ind = random.choice(unique_indices)
                    # print('    CHOSEN: ', unique2_name, unique2_ind, '(', used_unique, ')')
                    # print('    REFERE: ', name, ind, pos)

                    ## choose reference position
                    references = create_references()
                    unique2_pos, goal_pos = random.choice(sorted(references))
                    abs_unique2 = tuple(map(sum, zip(pos, unique2_pos)))
                    abs_goal = tuple(map(sum, zip(pos, goal_pos)))

                    while not self.__valid_position(world, abs_unique2) or not self.__valid_position(world, abs_goal):
                        unique2_pos, goal_pos = random.choice(sorted(references))
                        abs_unique2 = tuple(map(sum, zip(pos, unique2_pos)))
                        abs_goal = tuple(map(sum, zip(pos, goal_pos)))


                    # print('    POSITI: ', abs_unique2)
                    # print('    GOAL  : ', abs_goal)
                    unique_positions[unique2_name] = abs_unique2
                    used_unique.append(unique2_ind)
                    world = self.__place(world, abs_unique2, unique2_ind)

                    instructions = references[(unique2_pos, goal_pos)]

                    ## choose whether goal location is
                    ## non-unique object or empty cell (grass)
                    if np.random.rand() < nonunique_reference_probability:
                        nonunique_name, nonunique_ind = random.choice(nonunique_indices)
                        world = self.__place(world, abs_goal, nonunique_ind)
                        goal_name = nonunique_name
                    else:
                        goal_name = 'cell'

                    if not self.only_global:
                        for instr in instructions:
                            instr = instr.replace('<OBJ1>', name)
                            instr = instr.replace('<OBJ2>', unique2_name)
                            instr = instr.replace('<GOAL>', goal_name)
                            # print(instr)
                            directions[instr] = abs_goal

        '''
        < nonunique > closest to < unique >
        '''

        kernel = 1
        grass_ind = library.objects['grass']['index']
        for unique_name, unique_pos in unique_positions.items():
            row_low = max(0, unique_pos[0] - kernel)
            row_high = min(world.shape[0], unique_pos[0] + kernel)
            col_low = max(0, unique_pos[1] - kernel)
            col_high = min(world.shape[1], unique_pos[1] + kernel)
            focus = world[row_low:row_high+1, col_low:col_high+1]
            # print(focus)

            ## in-place shuffle of non-unique objects
            random.shuffle(nonunique_indices)
            # print(nonunique_indices)
            for (nonunique_name, nonunique_ind) in nonunique_indices:
                ## check if there is already non-unique object
                ## surrounding unique objects
                if (not (focus == nonunique_ind).any()) and (focus == grass_ind).any():
                    candidate_positions = np.argwhere(focus == grass_ind)
                    relative_position = random.choice(candidate_positions)
                    absolute_position = tuple(map(sum, zip(unique_pos, relative_position)))
                    if unique_pos[0] < kernel:
                        shift_row = unique_pos[0]
                    else:
                        shift_row = kernel

                    if unique_pos[1] < kernel:
                        shift_col = unique_pos[1]
                    else:
                        shift_col = kernel

                    absolute_position = tuple(map(sum, zip(absolute_position, (-shift_row, -shift_col))))

                    # print('UNIQUE: ', unique_pos)
                    # print('RELATIVE: ', relative_position)
                    # print('ABSOLUTE: ', absolute_position)
                    world = self.__place(world, absolute_position, nonunique_ind)
                    if not self.only_global:
                        instr = 'reach ' + nonunique_name + ' closest to ' + unique_name
                        directions[instr] = absolute_position
                    break
                else:
                    # print('FOUND', nonunique_ind, 'in focus')
                    pass

        '''
        reach northernmost < nonunique >
        '''

        for (name, ind) in nonunique_indices:
            # print(name, ind)
            positions = np.argwhere(world == ind).tolist()
            # print(positions)
            if len(positions) > 2:
                north = min(positions, key = lambda x: x[0])
                east = max(positions, key = lambda x: x[1])
                south = max(positions, key = lambda x: x[0])
                west = min(positions, key = lambda x: x[1])
                # print('north: ', north)
                # print('east: ', east)
                # print('south: ', south)
                # print('west: ', west)
                # instr = 'reach northernmost ' + nonunique_name
                directions['reach northernmost ' + name] = tuple(north)
                directions['reach easternmost ' + name] = tuple(east)
                directions['reach southernmost ' + name] = tuple(south)
                directions['reach westernmost ' + name] = tuple(west)

        # pdb.set_trace()

        reward_maps, terminal_maps, instructions, goals = \
            self.addRewards(world, unique_positions, directions)

        info = {
            'map': world,
            'rewards': reward_maps,
            'terminal': terminal_maps,
            'instructions': instructions,
            'goals': goals
        }
        return info

    def __puddles(self, iters, max_width=3, max_steps=8):
        (M,N) = self.shape
        turns = ['up', 'down', 'left', 'right']
        world = np.zeros( self.shape )
        world.fill( self.objects['puddle']['index'] )
        # position = np.floor(np.random.uniform(size=2)*self.shape[0]).astype(int)

        position = (np.random.uniform()*M, np.random.uniform()*N)
        position = list(map(int, position))

        for i in range(iters):
            direction = random.choice(turns)
            width = int(np.random.uniform(low=1, high=max_width))
            steps = int(np.random.uniform(low=1, high=max_steps))
            if direction == 'up':
                top = max(position[0] - steps, 0)
                bottom = position[0]
                left = max(position[1] - int(math.floor(width/2.)), 0)
                right = min(position[1] + int(math.ceil(width/2.)), N)
                position[0] = top
            elif direction == 'down':
                top = position[0]
                bottom = min(position[0] + steps, M)
                left = max(position[1] - int(math.floor(width/2.)), 0)
                right = min(position[1] + int(math.ceil(width/2.)), N)
                position[0] = bottom
            elif direction == 'left':
                top = max(position[0] - int(math.floor(width/2.)), 0)
                bottom = min(position[0] + int(math.ceil(width/2.)), M)
                left = max(position[1] - steps, 0)
                right = position[1]
                position[1] = left
            elif direction == 'right':
                top = max(position[0] - int(math.floor(width/2.)), 0)
                bottom = min(position[0] + int(math.ceil(width/2.)), M)
                left = position[1]
                right = min(position[1] + steps, N)
                position[1] = right
            # print(top, bottom, left, right, self.objects['grass']['index'])
            # print(world.shape)
            world[top:bottom+1, left:right+1] = self.objects['grass']['index']

        return world

    def addRewards(self, world, positions, directions):
        reward_maps = []
        terminal_maps = []
        instruction_set = []
        goal_positions = []

        object_values = np.zeros( self.shape )
        ## add non-background values
        for name, obj in self.objects.items():
            value = obj['value']
            if not obj['background'] and obj['unique']:
                pos = positions[name]
                object_values[pos] = value
            elif obj['background']:
                mask = np.ma.masked_equal(world, obj['index']).mask
                # print(name, obj['index'])
                # print(mask)
                # print(value)
                if mask.sum() > 0:
                    object_values[mask] += value
                # for st
                # value = obj['v']

        # print('values: ')
        # print(object_values)

        # for name, obj in self.objects.items():
            # if not obj['background']:
            # ind = obj['index']
            # pos = positions[name]
        for (phrase, target_pos) in  directions.items():
            rewards = object_values.copy()
            rewards[target_pos] += self.goal_value
            terminal = np.zeros( self.shape )
            terminal[target_pos] = 1

            reward_maps.append(rewards)
            terminal_maps.append(terminal)
            instruction_set.append(phrase)
            goal_positions.append(target_pos)

            # print(name, pos, direct)
        # print(reward_maps)
        # print(instruction_set)
        # print(goal_positions)
        return reward_maps, terminal_maps, instruction_set, goal_positions

    # def randomPosition(self):
    #     pos = tuple( (np.random.uniform(size=2) * self.dim).astype(int) )
    #     return pos

    def unique_directions(self, world, pos, name):
        directions = []
        for identifier, offset in self.unique_instructions.items():
            phrase = 'reach cell ' + identifier + ' ' + name
            absolute_pos = tuple(map(sum, zip(pos, offset)))
            # print(absolute_pos)
            (i,j) = absolute_pos
            (M,N) = self.shape
            out_of_bounds = (i < 0 or i >= M) or (j < 0 or j >= N)

            # absolute_pos[0] < 0 or absolute_pos[0] >  [coord < 0 or coord >= self.dim for coord in absolute_pos]
            if not out_of_bounds:
                in_puddle = world[absolute_pos] == self.objects['puddle']['index']
                if not in_puddle:
                    directions.append( (phrase, absolute_pos) )
        # print(directions)
        return directions

    def nonunique_single_directions(self, world, pos, name, unique_positions, kernel=3):
        unique_indices = [self.objects[name]['index'] for name in self.objects if not self.objects[name]['background'] and self.objects[name]['unique']]
        i,j = pos
        for di in range(-kernel+1, kernel):
            for dj in range(-kernel+1, kernel):
                x = i + di
                y = j + dj

                focus = world[x:x+kernel, y:y+kernel]
        pdb.set_trace()

    def global_directions(self, world, non_unique, unique):
        pass

        # for i in [-1, 0, 1]:
        #     for j in [-1, 0, 1]:
        #         if i == 0 and j == 0:
        #             pass
        #         else:


if __name__ == '__main__':
    for i in range(1):
        gen = NonUniqueGenerator(library.objects, library.unique_instructions, shape=(10,10), only_global=True)
        info = gen.new()

        print(info['map'])
        print(info['instructions'], len(info['instructions']))
        print(len(info['rewards']), len(info['terminal']))
        # print(info[''])
        # print(info['terminal'])



