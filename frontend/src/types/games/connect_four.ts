export interface ConnectFourConfig {
    rows: number        // default 6
    cols: number        // default 7
    win_length: number  // default 4
}

// Disc values as sent by the backend
export type Disc = 'R' | 'Y' | null

export interface LastMove {
    row: number
    col: number
    disc: Disc
    seat: number
}

export interface ConnectFourState {
    board: Disc[][]                      // null=empty, 'R'=seat 0, 'Y'=seat 1
    current_turn_seat: number            // 0 or 1
    seat_discs: Record<string, Disc>     // { '0': 'R', '1': 'Y' }
    move_count: number
    last_move: LastMove | null
    winner_seat: number | null
    outcome: string | null               // null | 'four_in_a_row' | 'board_full' | 'resign'
    status: 'active' | 'finished'
}
