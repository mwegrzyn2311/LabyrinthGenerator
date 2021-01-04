from PIL import Image
import random
import numpy as np
import math

values = ["None", "Wall", "TmpWall", "ExitPath", "NonExitPath"]
colorsBase = [(255, 255, 255), (0, 0, 0), (125, 125, 125), (194, 171, 109), (194, 171, 109)]
colorsNeat = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 255, 0), (194, 171, 109)]
colorsEyeSafe = [(255, 255, 255), (0, 0, 0), (125, 125, 125), (78, 177, 186), (194, 171, 109)]


class RandomLab:
    __neighbours = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    __tmp_walls = []
    __walls = []

    def __init__(self, width, height, straight_weight):
        self.width = width
        self.height = height
        self.straight_weight = straight_weight

        # Generate Empty Lab
        self.tiles = []
        # Lab is bounded, so first and last rows are full. Same applies to first and last column
        self.tiles.append(["Wall"] * width)
        for i in range(1, height - 1):
            row = ["Wall"]
            for j in range(1, width - 1):
                row.append("None")
            row.append("Wall")
            self.tiles.append(row)
        self.tiles.append(["Wall"] * width)

        # Generate entrance and exit
        self.entrance = (height - 1, random.randint(1, width - 1))
        self.tiles[self.entrance[0]][self.entrance[1]] = "None"

        self.exit = (0, random.randint(1, width - 1))
        self.tiles[self.exit[0]][self.exit[1]] = "None"

        self.__generate_exit_path()
        self.__generate_non_exit_paths()

    def write_lab_to_image(self, image_filename, colors_mode):
        pixels = []
        for rows in self.tiles:
            pixel_row = []
            for tile in rows:
                pixel_row.append(colors_mode[values.index(tile)])
            pixels.append(pixel_row)
        lab_array = np.array(pixels, dtype=np.uint8)
        lab_image = Image.fromarray(lab_array)
        lab_image.save(image_filename)

    def __is_path(self, y, x):
        return self.__is_in_lab(y, x) and (self.tiles[y][x] == "ExitPath" or self.tiles[y][x] == "NonExitPath")

    def __place_tmp_wall(self, y, x):
        if not self.__is_in_lab(y, x):
            return
        if self.tiles[y][x] == "None":
            self.tiles[y][x] = "TmpWall"
            self.__tmp_walls.append((y, x))
        elif self.tiles[y][x] == "TmpWall":
            self.tiles[y][x] = "Wall"
            self.__tmp_walls.remove((y, x))
            self.__walls.append((y, x))

    def __is_in_lab(self, y, x):
        return 0 <= y < self.height and 0 <= x < self.width

    def __generate_non_exit_paths(self):
        while len(self.__tmp_walls) >= 1:
            new_path_start = self.__tmp_walls.pop(random.randint(0, len(self.__tmp_walls) - 1))
            # Find direction
            (y, x) = new_path_start
            for neigh in self.__neighbours:
                (j, i) = neigh
                if self.__is_in_lab(y + j, x + i) and (
                        self.tiles[y + j][x + i] == "ExitPath" or self.tiles[y + j][x + i] == "NonExitPath"):
                    (dir_y, dir_x) = (-j, -i)

            # Get random path length
            # TODO: Consider changing ranges in randint
            if dir_y == 0:
                straight_len = random.randint(max(2, math.floor(self.width / 20)), max(4, math.floor(self.width / 4)))
            else:
                straight_len = random.randint(max(2, math.floor(self.height / 20)), max(4, math.floor(self.height / 4)))

            self.tiles[y][x] = "None"
            while straight_len > 0:
                if self.tiles[y][x] == "None":
                    self.tiles[y][x] = "NonExitPath"
                    if dir_y == 0:
                        self.__place_tmp_wall(y + 1, x)
                        self.__place_tmp_wall(y - 1, x)
                    else:
                        self.__place_tmp_wall(y, x + 1)
                        self.__place_tmp_wall(y, x - 1)
                    y += dir_y
                    x += dir_x
                    straight_len -= 1
                else:
                    break
            self.__place_tmp_wall(y, x)

    def __generate_exit_path(self):
        (curr_y, curr_x) = self.entrance
        (prev_j, prev_i) = (-1, 0)
        while (curr_y, curr_x) != self.exit:
            self.tiles[curr_y][curr_x] = "ExitPath"

            tmp_neighbours = self.__neighbours.copy()

            while True:
                if len(tmp_neighbours) == 4 and random.random() < self.straight_weight:
                    (j, i) = (prev_j, prev_i)
                    tmp_neighbours.remove((j, i))
                else:
                    index = random.randint(0, len(tmp_neighbours)-1)
                    (j, i) = tmp_neighbours.pop(index)

                accepted = False


                tmp_tmp_walls = []
                for neigh in self.__neighbours:
                    (n_y, n_x) = neigh
                    (w_y, w_x) = (curr_y + n_y, curr_x + n_x)
                    if self.__is_in_lab(w_y, w_x) and self.tiles[w_y][w_x] == "None" and (n_x, n_y) != (i, j):
                        self.tiles[w_y][w_x] = "TmpWall"
                        tmp_tmp_walls.append((w_y, w_x))

                if self.__is_in_lab(curr_y + j, curr_x + i) and self.tiles[curr_y + j][curr_x + i] == "None" and self.__exit_accessible(curr_y + j, curr_x + i):
                    accepted = True

                for tmp_tmp_wall in tmp_tmp_walls:
                    (w_y, w_x) = tmp_tmp_wall
                    self.tiles[w_y][w_x] = "None"

                if accepted:
                    break

            for neigh in self.__neighbours:
                (n_y, n_x) = neigh
                if self.__is_in_lab(curr_y + n_y, curr_x + n_x) and not (self.__is_path(curr_y + n_y, curr_x + n_x) or neigh == (j, i)):
                    self.__place_tmp_wall(curr_y + n_y, curr_x + n_x)

            prev_j = j
            prev_i = i
            curr_y = curr_y + j
            curr_x = curr_x + i
        self.tiles[curr_y][curr_x] = "ExitPath"

    def __exit_accessible(self, curr_y, curr_x):
        visited = [([False] * self.width) for _ in range(self.height)]
        tiles_to_visit = [(curr_y, curr_x)]
        visited[curr_y][curr_x] = True

        def dist_square(x_y):
            return (self.exit[0] - x_y[0]) ^ 2 + (self.exit[1] - x_y[1]) ^ 2

        while tiles_to_visit:
            (y, x) = tiles_to_visit.pop()
            # If exit was found
            if (y, x) == self.exit:
                return True
            # Add neighbours to stack if we can move to them and sort them by dist for optimization
            # TODO: Consider changing it so that there is no need to sort (for example: always up and either right or left based on position instead of all that multiplication stuff)
            accessible_neighbours = []
            for neigh in self.__neighbours:
                (j, i) = neigh
                if self.__is_in_lab(y+j, x+i) and not visited[y + j][x + i] and self.tiles[y + j][x + i] == "None":
                    accessible_neighbours.append((y + j, x + i))
                    visited[y + j][x + i] = True
            accessible_neighbours.sort(key=dist_square, reverse=True)
            for tile in accessible_neighbours:
                tiles_to_visit.append(tile)

        return False


if __name__ == '__main__':
    width = 50
    height = 50
    straightWeight = 0.6

    lab = RandomLab(width, height, straightWeight)
    lab.write_lab_to_image("lab.png", colorsBase)
    lab.write_lab_to_image("lab_alt.png", colorsNeat)
    lab.write_lab_to_image("lab_eye_safe.png", colorsEyeSafe)
