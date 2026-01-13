def get_successors(task_id, all_tasks, depth=0):
    # Safety recursion depth
    if depth > 50: return [] 
    succs = []
    for t in all_tasks:
        if task_id in t['Predecessors']:
            succs.append(t['Task'])
            succs.extend(get_successors(t['Task'], all_tasks, depth+1))
    return list(set(succs))

def solve_rpw(tasks, cycle_time):
    # Menghitung Bobot
    weighted_tasks = []
    for task in tasks:
        succs = get_successors(task['Task'], tasks)
        weight = task['Time'] + sum(t['Time'] for t in tasks if t['Task'] in succs)
        t_new = task.copy()
        t_new['Weight'] = weight
        weighted_tasks.append(t_new)

    # Urutkan berdasarkan Bobot
    sorted_tasks = sorted(weighted_tasks, key=lambda x: x['Weight'], reverse=True)
    
    # 3. Assignment Logic (Versi Anti-Freeze)
    stations = []
    current_station = {'id': 1, 'tasks': [], 'time_left': cycle_time}
    assigned = []
    loop_count = 0 

    while len(assigned) < len(tasks):
        loop_count += 1
        if loop_count > 1000: return "Error: Infinite Loop (Check Data Logic)"

        added = False
        for task in sorted_tasks:
            if task['Task'] in assigned: continue
            
            preds_ok = all(p in assigned for p in task['Predecessors'])
            time_ok = task['Time'] <= current_station['time_left']
            
            if preds_ok and time_ok:
                current_station['tasks'].append(task['Task'])
                current_station['time_left'] -= task['Time']
                assigned.append(task['Task'])
                added = True
                break
        
        if not added:
            # Jika stasiun kosong tapi tidak bisa isi task -> DEADLOCK
            if len(current_station['tasks']) == 0:
                return "Error: Tidak ada task yang bisa masuk (Cek Predecessor/Cycle Time)"
            
            stations.append(current_station)
            current_station = {'id': len(stations) + 1, 'tasks': [], 'time_left': cycle_time}
            
    if current_station['tasks']:
        stations.append(current_station)
    return stations
