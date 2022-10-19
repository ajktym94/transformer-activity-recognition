from torch.utils.data import Dataset
import numpy as np
import re

categories = ['Abuse','Arrest','Arson', 'Assault', 'Burglary','Explosion','Fighting','RoadAccidents','Robbery','Shooting','Shoplifting','Stealing','Vandalism']

UTK_categories = ['walk', 'sitDown', 'standUp', 'pickUp', 'carry', 'throw', 'push', 'pull', 'waveHands', 'clapHands']

NTU_categories = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'A17', 'A18', 'A19', 'A20', 'A21', 'A22', 'A23', 'A24', 'A25', 'A26', 'A27', 'A28', 'A29', 'A30', 'A31', 'A32', 'A33', 'A34', 'A35', 'A36', 'A37', 'A38', 'A39', 'A40', 'A41', 'A42', 'A43', 'A44', 'A45', 'A46', 'A47', 'A48', 'A49', 'A50', 'A51', 'A52', 'A53', 'A54', 'A55', 'A56', 'A57', 'A58', 'A59', 'A60', 'A61', 'A62', 'A63', 'A64', 'A65', 'A66', 'A67', 'A68', 'A69', 'A70', 'A71', 'A72', 'A73', 'A74', 'A75', 'A76', 'A77', 'A78', 'A79', 'A80', 'A81', 'A82', 'A83', 'A84', 'A85', 'A86', 'A87', 'A88', 'A89', 'A90', 'A91', 'A92', 'A93', 'A94', 'A95', 'A96', 'A97', 'A98', 'A99', 'A100', 'A101', 'A102', 'A103', 'A104', 'A105', 'A106', 'A107', 'A108', 'A109', 'A110', 'A111', 'A112', 'A113', 'A114', 'A115', 'A116', 'A117', 'A118', 'A119', 'A120']


def get_categories():
    return categories
    
def get_UTK_categories():
    return UTK_categories

def get_NTU_categories():
    return NTU_categories    

class Trajectory:
    def __init__(self, trajectory_id, frames, coordinates, category, dimension):
        self.trajectory_id = trajectory_id
        self.person_id = trajectory_id.split('_')[2][0] # Saves the person id in each video
        self.frames = frames
        self.coordinates = coordinates
        #self.is_global = False
        self.category = category #crime category: Abuse etc. 
        self.dimension = 2 if dimension=='2D' else 3

    def __len__(self):
        return len(self.frames)

    def is_short(self, input_length, input_gap, pred_length=0):
        min_trajectory_length = input_length + input_gap * (input_length - 1) + pred_length

        return len(self) < min_trajectory_length

class TrajectoryDataset(Dataset):
    """
    A dataset to store the trajectories. This should be more efficient than using just arrays.
    Also should be efficient with dataloaders.
    """
    def __init__(self, trajectory_ids, trajectory_videos, trajectory_persons, trajectory_frames, trajectory_categories, X):
        self.ids = [x[0] for x in trajectory_ids]
        print(type(trajectory_ids[0]))
        print(self.ids)
        self.videos = trajectory_videos
        self.persons = trajectory_persons
        self.frames = trajectory_frames
        self.categories = trajectory_categories
        self.coordinates = X

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, idx):
        data = {}
        data['id'] = self.ids[idx]
        data['videos'] = self.videos[idx]
        data['persons'] = self.persons[idx]
        data['frames'] = self.frames[idx]
        data['categories'] = self.categories[idx]
        data['coordinates'] = self.coordinates[idx]

        # return data
        return self.ids[idx], self.videos[idx], self.persons[idx], self.frames[idx],self.coordinates[idx], self.categories[idx]

    def trajectory_ids(self):
        return self.ids


def remove_short_trajectories(trajectories, input_length, input_gap, pred_length=0):
    filtered_trajectories = {}
    for trajectory_id, trajectory in trajectories.items():
        if not trajectory.is_short(input_length=input_length, input_gap=input_gap, pred_length=pred_length):
            filtered_trajectories[trajectory_id] = trajectory

    return filtered_trajectories
    
def split_into_train_and_test(trajectories, train_ratio=0.8, seed=42):
    np.random.seed(seed)

    trajectories_ids = []
    trajectories_lengths = []
    for trajectory_id, trajectory in trajectories.items():
        trajectories_ids.append(trajectory_id)
        trajectories_lengths.append(len(trajectory))

    sorting_indices = np.argsort(trajectories_lengths)
    q1_idx = round(len(sorting_indices) * 0.25)
    q2_idx = round(len(sorting_indices) * 0.50)
    q3_idx = round(len(sorting_indices) * 0.75)

    sorted_ids = np.array(trajectories_ids)[sorting_indices]
    train_ids = []
    val_ids = []
    quantiles_indices = [0, q1_idx, q2_idx, q3_idx, len(sorting_indices)]
    for idx, q_idx in enumerate(quantiles_indices[1:], 1):
        q_ids = sorted_ids[quantiles_indices[idx - 1]:q_idx]
        q_ids = np.random.permutation(q_ids)
        train_idx = round(len(q_ids) * train_ratio)
        train_ids.extend(q_ids[:train_idx])
        val_ids.extend(q_ids[train_idx:])

    trajectories_train = {}
    for train_id in train_ids:
        trajectories_train[train_id] = trajectories[train_id]

    trajectories_val = {}
    for val_id in val_ids:
        trajectories_val[val_id] = trajectories[val_id]

    return trajectories_train, trajectories_val


#extract fixed sized segments using sliding window to create equal length input
def extract_fixed_sized_segments(dataset, trajectories, input_length):
    trajectories_ids, videos, persons, frames, categories, X = [], [], [], [], [], []
    
    #print('FORMAT trajectories_ids {}'.format(type(trajectories_ids)))
        
    for trajectory in trajectories.values():
        traj_ids, video_ids, person_ids, traj_frames, traj_categories, traj_X = _extract_fixed_sized_segments(dataset, trajectory, input_length)
        
        #print('traj_ids type', type(traj_ids))
        trajectories_ids.append(traj_ids)
        frames.append(traj_frames)
        categories.append(traj_categories)
        X.append(traj_X)
        videos.append(video_ids)
        persons.append(person_ids)
        
    trajectories_ids, videos, persons, frames, categories, X = np.vstack(trajectories_ids), np.vstack(videos), np.vstack(persons), np.vstack(frames), np.vstack(categories), np.vstack(X)


    return trajectories_ids, videos, persons, frames, categories, X


def _extract_fixed_sized_segments(dataset, trajectory, input_length):
    traj_frames, traj_X = [], []

    trajectory_id = trajectory.trajectory_id
    coordinates = trajectory.coordinates
    frames = trajectory.frames
    category = trajectory.category

    #print('frames',frames)

    total_input_seq_len = input_length
    stop = len(coordinates) - total_input_seq_len + 1
    #print('total_input_seq_len', total_input_seq_len)
    #print('len(coordinates)',len(coordinates))
    #print('stop',stop)
    
    for start_index in range(stop):
        stop_index = start_index + total_input_seq_len
        traj_X.append(coordinates[start_index:stop_index, :])
        traj_frames.append(frames[start_index:stop_index])
    
    traj_frames, traj_X = np.stack(traj_frames, axis=0), np.stack(traj_X, axis=0)

    
    traj_ids = np.full(traj_frames.shape, fill_value=trajectory_id)
    traj_categories = np.full(traj_frames.shape, fill_value=category)
    
    #print('traj_ids:', traj_ids)
    #print('traj_categories:',traj_categories)
    
    if dataset == "HR-Crime":
        numbers_found = re.search(r"(\d+)_(\d+)", trajectory_id)
        video_id = numbers_found.group(1)
        person_id = numbers_found.group(2)
    elif dataset == "UTK":
        numbers_found = re.search(r"_(\w+)_(\w+)", trajectory_id)
        video_id = numbers_found.group(1)[1:]
        person_id = numbers_found.group(2)[1:]
    # elif dataset == "NTU":
    #     numbers_found = re.search(r"(\d+)_(\d+)", trajectory_id)
    #     video_id = numbers_found.group(1)
    #     person_id = numbers_found.group(2)
    elif "NTU" in dataset:
        # video_id = trajectory_id.split('_')[0]+trajectory_id.split('_')[1]+trajectory_id.split('_')[2][1:]
        video_id = 1#trajectory_id.split('_')[2][0]
        person_id = 1#trajectory_id.split('_')[2][0]
    
    #print('trajectory_id',trajectory_id)
    #print('numbers_found', numbers_found)
    
    #print('video_id', int(video_id))
    #print('person_id', int(person_id))
    
    traj_videos = np.full(traj_frames.shape, fill_value=video_id)
    traj_persons = np.full(traj_frames.shape, fill_value=int(person_id))
    
    #print('traj_videos', traj_videos)
    #print('traj_persons', traj_persons)

    return traj_ids, traj_videos, traj_persons, traj_frames, traj_categories, traj_X

#extract fixed sized segments using sliding window to create equal length input
def extract_fixed_sized_segments_UTK(dataset, trajectories, input_length):
    trajectories_ids, videos, persons, frames, categories, X = [], [], [], [], [], []
    
    #print('FORMAT trajectories_ids {}'.format(type(trajectories_ids)))
        
    for trajectory in trajectories.values():
        traj_ids, video_ids, person_ids, traj_frames, traj_categories, traj_X = _extract_fixed_sized_segments_UTK(dataset, trajectory, input_length)
        
        #print('traj_ids type', type(traj_ids))
        trajectories_ids.append(traj_ids)
        frames.append(traj_frames)
        categories.append(traj_categories)
        X.append(traj_X)
        videos.append(video_ids)
        persons.append(person_ids)
        
    trajectories_ids, videos, persons, frames, categories, X = np.vstack(trajectories_ids), np.vstack(videos), np.vstack(persons), np.vstack(frames), np.vstack(categories), np.vstack(X)


    return trajectories_ids, videos, persons, frames, categories, X


def _extract_fixed_sized_segments_UTK(dataset, trajectory, input_length):
    traj_frames, traj_X = [], []

    trajectory_id = trajectory.trajectory_id
    coordinates = trajectory.coordinates
    frames = trajectory.frames
    category = trajectory.category

    #print('frames',frames)

    total_input_seq_len = input_length
    stop = len(coordinates) - total_input_seq_len + 1
    #print('total_input_seq_len', total_input_seq_len)
    #print('len(coordinates)',len(coordinates))
    #print('stop',stop)
    
    for start_index in range(stop):
        stop_index = start_index + total_input_seq_len
        traj_X.append(coordinates[start_index:stop_index, :])
        traj_frames.append(frames[start_index:stop_index])
    
    traj_frames, traj_X = np.stack(traj_frames, axis=0), np.stack(traj_X, axis=0)

    
    traj_ids = np.full(traj_frames.shape, fill_value=trajectory_id)
    traj_categories = np.full(traj_frames.shape, fill_value=category)
    
    #print('traj_ids:', traj_ids)
    #print('traj_categories:',traj_categories)
    #print('trajectory_id',trajectory_id)

    numbers_found = re.search(r"_(\w+)_(\w+)", trajectory_id)
    
    #print('numbers_found', numbers_found)
    
    video_id = numbers_found.group(1)
    person_id = numbers_found.group(2)
    
    #print('video_id', int(video_id[1:]))
    #print('person_id', int(person_id[1:]))
    
    traj_videos = np.full(traj_frames.shape, fill_value=int(video_id[1:]))
    traj_persons = np.full(traj_frames.shape, fill_value=int(person_id[1:]))
    
    #print('traj_videos', traj_videos)
    #print('traj_persons', traj_persons)

    return traj_ids, traj_videos, traj_persons, traj_frames, traj_categories, traj_X