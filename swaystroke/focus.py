import i3ipc

def get_focus_history(node, history_list):
    """Recursively build an ordered list of container IDs based on focus history."""
    if hasattr(node, 'focus'):
        for f_id in node.focus:
            history_list.append(f_id)
            # Find the child node with this id to traverse deeper
            child = next((c for c in node.nodes + node.floating_nodes if c.id == f_id), None)
            if child:
                get_focus_history(child, history_list)

def focus_window_at(x, y):
    try:
        i3 = i3ipc.Connection()
        tree = i3.get_tree()
        workspaces = i3.get_workspaces()
        visible_ws_names = [ws.name for ws in workspaces if ws.visible]
        
        tiled_candidates = []
        floating_candidates = []
        
        # 1. Collect all tiled candidates
        for leaf in tree.leaves():
            ws = leaf.workspace()
            if ws and ws.name in visible_ws_names:
                if leaf.rect.x <= x <= leaf.rect.x + leaf.rect.width and \
                   leaf.rect.y <= y <= leaf.rect.y + leaf.rect.height:
                    tiled_candidates.append(leaf)
                    
        # 2. Collect all floating candidates along with their Z-index
        for node in tree.workspaces():
            if node.name in visible_ws_names:
                # In Sway/i3, floating_nodes are ordered from bottom to top visually.
                # So a higher index means it is rendered ON TOP.
                for z_index, floating_con in enumerate(node.floating_nodes):
                    # Check the floating container itself (which might be the window)
                    if floating_con.rect.x <= x <= floating_con.rect.x + floating_con.rect.width and \
                       floating_con.rect.y <= y <= floating_con.rect.y + floating_con.rect.height:
                        
                        # Find the deepest leaf inside the floating con
                        found_leaf = False
                        for leaf in floating_con.leaves():
                            if leaf.rect.x <= x <= leaf.rect.x + leaf.rect.width and \
                               leaf.rect.y <= y <= leaf.rect.y + leaf.rect.height:
                                floating_candidates.append((leaf, z_index))
                                found_leaf = True
                                
                        if not found_leaf:
                             floating_candidates.append((floating_con, z_index))

        # 3. Resolve overlaps
        best_target = None

        if floating_candidates:
            # If there are floating candidates, they are ALWAYS visually above tiled windows.
            # We sort them by their Z-index (the index in the floating_nodes array).
            # The highest Z-index is the one physically rendered on top.
            best_target = max(floating_candidates, key=lambda c: c[1])[0]

        elif tiled_candidates:
            # If there are only tiled candidates, we use focus history as a tie-breaker.
            # Build a global ordered list of container IDs based on recent focus
            history = []
            get_focus_history(tree, history)
            
            best_rank = float('inf')
            for candidate in tiled_candidates:
                try:
                    rank = history.index(candidate.id)
                except ValueError:
                    rank = float('inf')
                    
                if rank < best_rank:
                    best_rank = rank
                    best_target = candidate

            # Fallback if no tiled candidate is in the history (rare)
            if not best_target:
                best_target = tiled_candidates[-1]

        else:
            return False

        print(f"Focusing window: {best_target.name} (id={best_target.id})")
        i3.command(f"[con_id={best_target.id}] focus")
        return True

    except Exception as e:
        print(f"Error focusing window: {e}")
    
    return False
