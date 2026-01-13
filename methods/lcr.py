def solve_lcr(tasks, cycle_time):
    # Urutkan Waktu Terbesar ke Terkecil
    sorted_tasks = sorted(tasks, key=lambda x: x['Time'], reverse=True)
    
    stations = []
    current_station = {'id': 1, 'tasks': [], 'time_left': cycle_time}
    assigned = []
    
    # Batas loop max 1000 
    loop_count = 0 
    
    while len(assigned) < len(tasks):
        loop_count += 1
        if loop_count > 1000:
            return "Error: Terjadi Infinite Loop. Cek apakah ada Predecessor yang salah ketik atau melingkar (A butuh B, B butuh A)."

        added = False
        for task in sorted_tasks:
            if task['Task'] in assigned: continue
            
            # Cek Predecessors
            preds_ok = all(p in assigned for p in task['Predecessors'])
            # Cek Waktu
            time_ok = task['Time'] <= current_station['time_left']
            
            if preds_ok and time_ok:
                current_station['tasks'].append(task['Task'])
                current_station['time_left'] -= task['Time']
                assigned.append(task['Task'])
                added = True
                break # Restart loop 
        
        if not added:
            # Jika stasiun masih kosong tapi tidak ada tugas yang masuk
            # Berarti tidak ada task yang memenuhi syarat (macet total)
            if len(current_station['tasks']) == 0:
                remaining = [t['Task'] for t in tasks if t['Task'] not in assigned]
                return f"Error: Macet pada task {remaining}. Mungkin Cycle Time terlalu kecil atau Predecessor salah."

            # Jika stasiun sudah ada isinya tapi tidak muat lagi, buat stasiun baru
            stations.append(current_station)
            current_station = {'id': len(stations) + 1, 'tasks': [], 'time_left': cycle_time}
    
    # Tambahkan stasiun terakhir jika ada tugas
    if current_station['tasks']:
        stations.append(current_station)
        
    return stations