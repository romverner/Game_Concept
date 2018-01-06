import copy
import time
import random
import threading

from player import Player

class Map_Manager():
  # class to update the map at the start of each turn and as turns progress
  _WALL       = 0
  _FLOOR      = 1
  _ITEM       = 2
  _PROJECTILE = 3
  _PLAYER     = 4

  def __init__(self,width,height):
    # initialize the map manager with map size
    self.mapsLock    = threading.Lock()
    self.init_map(width,height)
    self.myPlayer    = Player(xPos=4,yPos=1,gold=0)
    self.width       = width
    self.height      = height
    with self.mapsLock:
      self.originalMap[self.myPlayer.xPos][self.myPlayer.yPos] = self._FLOOR
      self.currentMap  = [col[:] for col in self.originalMap]
      self.currentMap[self.myPlayer.xPos][self.myPlayer.yPos] = self._PLAYER

  def get_pixel(self,x,y):
    with self.mapsLock:
      #print 'get_pixel has lock'
      return self.currentMap[x][y]

  def weighted_map_number_generator(self):
    # Returns one of the Map_Manager pre-defined constants.
    # _WALL weight = 0.33, _FLOOR weight = ~0.645, _ITEM weight = ~0.025
    val_one = random.random()
    if val_one >= 0 and val_one < 0.33:
      return self._WALL
    elif val_one >= 0.33 and val_one < 0.975:
      return self._FLOOR
    elif val_one >= 0.975:
      return self._ITEM

  def init_map(self,width=16,height=16):
    # create a map for the start of play
    with self.mapsLock:
      print 'init_map has lock'
      self.originalMap = []
      for x in xrange(width):
        self.originalMap.append([])
        for y in xrange(height):
          if x==0 or y==0 or x==width-1 or y==height-1:
            self.originalMap[x].append(self._WALL)
          else:
            self.originalMap[x].append(self.weighted_map_number_generator())

  def redraw_map(self):
    self.init_map(self.width,self.height)
    with self.mapsLock:
      print 'redraw_map has lock'
      self.originalMap[self.myPlayer.xPos][self.myPlayer.yPos] = self._FLOOR
      self.currentMap  = [col[:] for col in self.originalMap]
      self.currentMap[self.myPlayer.xPos][self.myPlayer.yPos] = self._PLAYER
    
  def _is_wall(self,x,y):
      if self._is_in_bounds(x,y):
        with self.mapsLock:
          print '_is_wall has lock'
          return self.currentMap[x][y] == self._WALL
      else:
        return True

  def _is_item(self,x,y):
    if self._is_in_bounds(x,y):
      with self.mapsLock:
        print '_is_item has lock'
        return self.currentMap[x][y] == self._ITEM
    else:
      return False

  def _is_empty(self,x,y):
    if self._is_in_bounds(x,y):
      with self.mapsLock:
        print '_is_empty has lock'
        return self.currentMap[x][y] == self._FLOOR
    else:
      return False

  def _is_in_bounds(self,x,y):
    """Checks in-bound paramters."""
    return x >= 0 and y >= 0 and x < self.width and y < self.height

  def track_projectile(self):
    new_proj = self.myPlayer.shoot_projectile()
    p_t      = threading.Thread(target=self.projectile_thread,
                                kwargs={'proj':new_proj})
    p_t.start()


  def projectile_thread(self,proj):
    while proj._is_alive():
      print 'projectile_thread has lock'
      old_x    = proj.get_x_position()
      old_y    = proj.get_y_position()
      proj.calc_next_position()
      proj_x   = proj.get_x_position()
      proj_y   = proj.get_y_position()
      if self._is_wall(proj_x,proj_y):
        proj._kill()
        with self.mapsLock:
          print 'projectile_thread has lock'
          self.originalMap[proj_x][proj_y] = self._FLOOR
          self.currentMap[proj_x][proj_y]  = self._FLOOR
      elif self._is_item(proj_x,proj_y) or self._is_empty(proj_x,proj_y):
        with self.mapsLock:
          print 'projectile_thread has lock'
          self.currentMap[proj_x][proj_y]  = self._PROJECTILE
      with self.mapsLock:
        print 'projectile_thread has lock'
        self.currentMap[old_x][old_y] = self.originalMap[old_x][old_y]
        self.currentMap[self.myPlayer.xPos][self.myPlayer.yPos] = self._PLAYER

      time.sleep(proj.get_refresh_time())

  def move_player(self,char):
    """ Tracks the player's movement based on keypresses and prevents illegal moves.
        Keeps track of 'item' tiles and moves them to player inventory."""
    old_x = self.myPlayer.get_x_position()
    old_y = self.myPlayer.get_y_position()
    self.myPlayer.player_movement(movement=char)
    new_x = self.myPlayer.get_x_position()
    new_y = self.myPlayer.get_y_position()

    if not self._is_in_bounds(new_x,new_y):
      new_x = old_x
      new_y = old_y
      self.myPlayer.set_x_position(old_x)
      self.myPlayer.set_y_position(old_y)
    elif self._is_wall(new_x,new_y):
      new_x = old_x
      new_y = old_y
      self.myPlayer.set_x_position(old_x)
      self.myPlayer.set_y_position(old_y)
    elif self._is_item(new_x,new_y):
      with self.mapsLock:
        print 'move_player has lock'
        self.originalMap[new_x][new_y] = self._FLOOR

      # Tracking gold acquired done here.
      self.myPlayer.acquire_gold(random.randint(1,2))
      gold_amount = self.myPlayer.get_gold_amount()
      print gold_amount
    with self.mapsLock:
      print 'move player has lock'
      self.currentMap[old_x][old_y] = self.originalMap[old_x][old_y]
      self.currentMap[new_x][new_y] = self._PLAYER