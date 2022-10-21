 #!/bin/env python
 
 #import packages
from itertools import count
import os
from csv import reader
import numpy as np
import pickle
from trajectory import Trajectory, get_NTU_categories, remove_short_trajectories, split_into_train_and_test
from utils import SetupLogger

logger = SetupLogger('logger')

# dimension = '2D'
dimension = '3D'

path = '/home/s2435462/HRC/NTU/skeleton/trajectory_csv_'+dimension       

def load_trajectories(trajectories_path, classes):
  trajectories = {}
  categories = os.listdir(trajectories_path)

  count_t = 0
  for category in categories:
      category_path = os.path.join(trajectories_path, category) # Path for each category
      folder_names = os.listdir(category_path) # List of folders inside the action class directory
      
      if "Normal" not in category:
        for folder_name in folder_names: # Loop through person folders inside action class directory
            logger.info('load trajectories for video: %s', folder_name)
            folder_path = os.path.join(category_path, folder_name) # Path to person folder
            csv_file_names = os.listdir(folder_path)  # CSV files inside the person folder
            for csv_file_name in csv_file_names: # Loop through csv files inside the person folder
                trajectory_file_path = os.path.join(folder_path, csv_file_name) # Path to trajectory CSV file
                logger.info(trajectory_file_path)
                try:
                  trajectory = np.loadtxt(trajectory_file_path, dtype=np.float32, delimiter=',', ndmin=2) # Load csv using loadtxt
                  count_t +=1
                except:
                  continue
                trajectory_frames, trajectory_coordinates = trajectory[:, 0].astype(np.int32), trajectory[:, 1:]
                trajectory_id = csv_file_name.split('.')[0]
                category_index = classes.index('A'+category[1:].lstrip('0'))
                
                #print('category_index',category_index)
                trajectories[trajectory_id] = Trajectory(trajectory_id=trajectory_id,
                                                        frames=trajectory_frames,
                                                        coordinates=trajectory_coordinates,
                                                        category = category_index,
                                                        dimension = dimension)

  logger.info('count = %d', count_t)
  return trajectories

all_categories = get_NTU_categories()
logger.info("categories: %s", str(all_categories))

#load trajectories
trajectories = load_trajectories(path, all_categories)
logger.info('Loaded %d trajectories.', len(trajectories))

#save trajectories
PIK = "/home/s2435462/HRC/data/trajectories_NTU_new_"+dimension+".dat"

with open(PIK, "wb") as f:
  pickle.dump(trajectories, f)

#remove short trajectories
trajectories = remove_short_trajectories(trajectories, input_length=12, input_gap=0, pred_length=12)

logger.info('Removed short trajectories. Number of trajectories left: %d.', len(trajectories))

#split trajectories into train and test
trajectories_train, trajectories_test = split_into_train_and_test(trajectories, train_ratio=0.8, seed=42)
logger.info('%d train trajectories and %d test trajectories', len(trajectories_train), len(trajectories_test))

#save trajectories for train and test
PIK_train = "/home/s2435462/HRC/data/trajectories_train_NTU_new_"+ dimension +".dat"
PIK_test = "/home/s2435462/HRC/data/trajectories_test_NTU_new_"+ dimension +".dat"

with open(PIK_train, "wb") as f:
  pickle.dump(trajectories_train, f)
 
with open(PIK_test, "wb") as f:
  pickle.dump(trajectories_test, f)


logger.info("Saved train and test trajectories.")