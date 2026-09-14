"""
Core algorithms ported from the original nea_oop.py.
These are kept as close to the original logic as possible (same maths,
same behaviour) but with every input()/print() call removed so they can
be driven by a web UI instead of a console menu.
"""
import random
from datetime import datetime, date

positionsList = ['GK', 'CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'CAM', 'CM', 'LM', 'RM', 'ST', 'LW', 'RW']

# Which positions can reasonably deputise for which (originally built inline
# inside Position.__init__).
def similar_positions(position_name):
    similar = []
    if position_name in ['CB', 'RB', 'LB']:
        similar.extend(['CB', 'RB', 'LB'])
    if position_name in ['RB', 'LB']:
        similar.extend(['LWB', 'RWB'])
    if position_name in ['CB', 'CDM']:
        similar.extend(['CB', 'CDM'])
    if position_name in ['CAM', 'CM', 'RM', 'LM', 'CDM']:
        similar.extend(['CAM', 'CM', 'RM', 'LM', 'CDM'])
    if position_name in ['RM', 'LM', 'RW', 'LW']:
        similar.extend(['RM', 'LM', 'RW', 'LW'])
    if position_name in ['RW', 'LW', 'RWB', 'LWB']:
        similar.extend(['RW', 'LW', 'RWB', 'LWB'])
    if position_name in ['CAM', 'ST']:
        similar.extend(['CAM', 'ST'])
    if position_name == 'ST':
        similar.extend(['LW', 'RW'])
    return similar


def add_to_priority_queue(element, priority_queue):
    """element = [rank, value]. Lower rank = higher priority (1 is best).
    Inserts to keep the queue sorted ascending by rank (stable - ties keep
    insertion order). This is a cleaned-up version of the original
    insertion-sort logic, which had an off-by-one bug at the list boundary."""
    position = 0
    while position < len(priority_queue) and priority_queue[position][0] <= element[0]:
        position += 1
    priority_queue.insert(position, element)


def remove_from_priority_queue(element_value, priority_queue):
    for item in list(priority_queue):
        if item[1] == element_value:
            priority_queue.remove(item)


def generate_formations(team_num):
    """Generates all possible (and plausible) formations for a given team size."""
    f_list = []
    max_defenders = team_num
    if team_num <= 7:
        for defenders in range(1, team_num):
            forwards = team_num - defenders - 1
            if defenders <= 4 and forwards <= 4:
                f_list.append(['{}-{}'.format(defenders, forwards), (defenders / (team_num - 1)), (forwards / (team_num - 1))])
                max_defenders = team_num
    else:
        max_defenders = 6
    for defenders in range(2, max_defenders):
        for midfielders in range(1, team_num - defenders - 1):
            forwards = team_num - defenders - midfielders - 1
            if forwards == 1 and midfielders == 1:
                pass
            else:
                if forwards >= 1 and forwards <= 4 and midfielders <= 5:
                    f_list.append(['{}-{}-{}'.format(defenders, midfielders, forwards),
                                    (defenders + midfielders * 0.5) / (team_num - 1),
                                    (forwards + midfielders * 0.5) / (team_num - 1)])
    if team_num > 9:
        for defenders in range(3, 6):
            dm = team_num - defenders - 5
            f_list.append(['{}-{}-3-1'.format(defenders, dm),
                            (defenders + dm * 0.5) / (team_num - 1),
                            (4 + dm * 0.5) / (team_num - 1)])
    return f_list


def make_positions_list(formation):
    """Flat list of position names for a formation, in GK->defence->mid->attack order (GK not included)."""
    lines = [int(chr) for chr in formation if chr != '-']
    formation_list = []
    if lines[0] == 2:
        formation_list.append(['LB', 'RB'])
    elif lines[0] == 3:
        formation_list.append(['LB', 'CB', 'RB'])
    elif lines[0] == 4:
        formation_list.append(['LB', 'CB', 'CB', 'RB'])
    else:
        formation_list.append(['LWB', 'CB', 'CB', 'CB', 'RWB'])
    if len(lines) == 3:
        if lines[1] == 1:
            formation_list.append(['CM'])
        elif lines[1] == 2:
            formation_list.append(['LM', 'RM'])
        elif lines[1] == 3:
            formation_list.append(['LM', 'CM', 'RM'])
        elif lines[1] == 4:
            formation_list.append(['LM', 'CM', 'CM', 'RM'])
        else:
            formation_list.append(['LM', 'CM', 'CM', 'CM', 'RM'])
    elif len(lines) == 4:
        if lines[1] == 2:
            formation_list.append([['CDM', 'CDM'], ['LW', 'CAM', 'RW']])
        elif lines[1] == 3:
            formation_list.append([['CDM', 'CDM', 'CDM'], ['LW', 'CAM', 'RW']])
    if lines[-1] == 1:
        formation_list.append(['ST'])
    elif lines[-1] == 2:
        formation_list.append(['ST', 'ST'])
    elif lines[-1] == 3:
        formation_list.append(['LW', 'ST', 'RW'])
    else:
        formation_list.append(['LW', 'ST', 'ST', 'RW'])
    # Flatten to a single list of position names (matches original usage in makeLineupWithPriorityQueue)
    flat = []
    for group in formation_list:
        for item in group:
            if isinstance(item, list):
                flat.extend(item)
            else:
                flat.append(item)
    return flat


def make_positions_array(formation):
    """Row-by-row (defence/mid/attack) array of position names, for pitch display."""
    lines = [int(chr) for chr in formation if chr != '-']
    if lines[0] == 2:
        defence = ['LB', 'RB']
    elif lines[0] == 3:
        defence = ['LB', 'CB', 'RB']
    elif lines[0] == 4:
        defence = ['LB', 'CB', 'CB', 'RB']
    else:
        defence = ['LWB', 'CB', 'CB', 'CB', 'RWB']
    if lines[-1] == 1:
        upfront = ['ST']
    elif lines[-1] == 2:
        upfront = ['ST', 'ST']
    elif lines[-1] == 3:
        upfront = ['LW', 'ST', 'RW']
    else:
        upfront = ['LW', 'ST', 'ST', 'RW']
    midfield = []
    if len(lines) == 3:
        if lines[1] == 1:
            midfield = ['CM']
        elif lines[1] == 2:
            midfield = ['LM', 'RM']
        elif lines[1] == 3:
            midfield = ['LM', 'CM', 'RM']
        elif lines[1] == 4:
            midfield = ['LM', 'CM', 'CM', 'RM']
        else:
            midfield = ['LM', 'CM', 'CM', 'CM', 'RM']
    elif len(lines) == 4:
        if lines[1] == 2:
            midfield = [['CDM', 'CDM'], ['LW', 'CAM', 'RW']]
        elif lines[1] == 3:
            midfield = [['CDM', 'CDM', 'CDM'], ['LW', 'CAM', 'RW']]
    return [defence, midfield, upfront]


def cluster(records, team_num):
    """K-means style clustering of formation records by (defensive, offensive) split.
    records: list of (FormationID, Formation, Defensive, Offensive) tuples.
    Returns (centroids, clusters)."""
    clusters = []
    if team_num < 7:
        k = 2
    elif team_num < 9:
        k = 3
    else:
        k = 4
    for _ in range(k):
        clusters.append([])

    centroids = []
    if len(records) == 0:
        return (centroids, clusters)
    if len(records) < k:
        k = len(records)
        clusters = clusters[:k]

    chosen_idx = set()
    while len(centroids) < k:
        c = random.randint(0, len(records) - 1)
        if c not in chosen_idx:
            chosen_idx.add(c)
            centroids.append(records[c])
    for x in range(k):
        clusters[x].append(centroids[x])
    for y in records:
        if y not in centroids:
            dist = float('inf')
            closest = 0
            for z in range(k):
                d = (y[2] - centroids[z][2]) ** 2 + (y[3] - centroids[z][3]) ** 2
                if d < dist:
                    dist = d
                    closest = z
            clusters[closest].append(y)

    converged = False
    new_centroids = [[c[2], c[3]] for c in centroids]
    safety = 0
    while not converged and safety < 100:
        safety += 1
        new_centroids = []
        for c in clusters:
            if len(c) == 0:
                new_centroids.append([0, 0])
                continue
            c1 = sum(b[2] for b in c)
            c2 = sum(b[3] for b in c)
            new_centroids.append([round(c1 / len(c), 3), round(c2 / len(c), 3)])
        old_as_pairs = [[c[0], c[1]] if isinstance(c[0], (int, float)) else [c[2], c[3]] for c in centroids]
        if new_centroids == old_as_pairs:
            converged = True
        else:
            centroids = new_centroids
            for count in range(len(clusters)):
                clusters[count] = []
            for r in records:
                dist = float('inf')
                closest = 0
                for a in range(k):
                    d = (r[2] - new_centroids[a][0]) ** 2 + (r[3] - new_centroids[a][1]) ** 2
                    if d < dist:
                        dist = d
                        closest = a
                clusters[closest].append(r)
    return (new_centroids, clusters)


def get_season_start_date():
    today = datetime.today()
    if today.month >= 8:
        return date(today.year, 8, 1)
    else:
        return date(today.year - 1, 8, 1)
