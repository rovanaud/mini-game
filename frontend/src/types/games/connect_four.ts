export interface ConnectFourConfig {
    rows: number        // default 6
    cols: number        // default 7
    win_length: number  // default 4
}

export interface ConnectFourState {
    board: number[][]   // 0=empty, 1=player1, 2=player2
    current_player: number
    winner: number | null      // null if game ongoing
    winning_cells: [number, number][] | null  // for highlight later
}
