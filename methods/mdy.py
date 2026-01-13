def solve_mdy(tasks, cycle_time):
    # Urutkan Time Terbesar 
    sorted_tasks = sorted(tasks, key=lambda x: x['Time'], reverse=True)
    
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
            # Jika stasiun kosong tapi macet -> DEADLOCK
            if len(current_station['tasks']) == 0:
                return "Error: Deadlock. Cek apakah ada predecessor yang tidak valid."
                
            stations.append(current_station)
            current_station = {'id': len(stations) + 1, 'tasks': [], 'time_left': cycle_time}
            
    if current_station['tasks']:
        stations.append(current_station)
    return stations