from iconservice import *

TAG = 'Colors'
ICX = 1000000000000000000
BET_MIN = 0.1*ICX
SIDE_BET_TYPES = ["specific_double", "specific_triple", "any_triple"]
SIDE_BET_MULTIPLIERS = [10, 180, 30]
main_bet_limit = 100*ICX
side_bet_limit = 10*ICX

# An interface to roulette score
class RouletteInterface(InterfaceScore):
    @interface
    def get_treasury_min(self) -> int:
        pass

    @interface
    def take_wager(self, _amount: int) -> None:
        pass

    @interface
    def wager_payout(self, _payout: int) -> None:
        pass

class Colors(IconScoreBase):
    _GAME_ON = "game_on"
    _ROULETTE_SCORE = 'roulette_score'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._game_on = VarDB(self._GAME_ON, db, value_type=bool)
        self._roulette_score = VarDB(self._ROULETTE_SCORE, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=1)
    def RollsResult(self, results: str):
        pass

    @eventlog(indexed=2)
    def MainBet(self, main_bet_win: str, m_payout: str):
        pass

    @eventlog(indexed=2)
    def SideBet(self, side_bet_win: str, s_payout: str):
        pass

    @eventlog(indexed=1)
    def TotalPayoutAmount(self, payout: str):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, recipient: Address, amount: int, note: str):
        pass

    @external
    def set_roulette_score(self, _scoreAddress: Address) -> None:
        if self.msg.sender != self.owner:
            revert('Only the owner can call the set_roulette_score method')
        self._roulette_score.set(_scoreAddress)

    @external(readonly=True)
    def get_roulette_score(self) -> Address:
        return self._roulette_score.get()

    @external
    def toggle_game_status(self) -> None:
        if self.msg.sender != self.owner:
            revert('Only the owner can call the game_on method')
        if self._roulette_score.get() is not None:
            self._game_on.set(not self._game_on.get())

    @external(readonly=True)
    def get_game_status(self) -> bool:
        return self._game_on.get()

    @external(readonly=True)
    def get_score_owner(self) -> Address:
        return self.owner

    def get_random(self, user_seed: str = '') -> int:
        Logger.debug(f'Entered get_random.', TAG)
        seed = (str(bytes.hex(self.tx.hash)) + str(self.now()) + user_seed)
        spin = int.from_bytes(sha3_256(seed.encode()), "big")
        Logger.debug(f'Result of the spin was {spin}.', TAG)
        return spin

    @payable
    @external
    def call_bet(self, yellow: int, white: int, pink: int, blue: int, red: int, green: int, s_yellow: int, s_white: int,
                 s_pink: int, s_blue: int, s_red: int, s_green: int, side_bet_type: str = '', user_seed: str = '') -> None:
        return self.bet(yellow, white, pink, blue, red, green, s_yellow, s_white, s_pink, s_blue, s_red, s_green,
                          side_bet_type, user_seed)

    def bet(self, yellow: int, white: int, pink: int, blue: int, red: int, green: int,
            s_yellow: int, s_white: int, s_pink: int, s_blue: int, s_red: int, s_green: int,
            side_bet_type: str = '', user_seed: str = '') -> None:
        main_bet_amount = yellow + white + pink + blue + red + green
        side_bet_amount = s_yellow + s_white + s_pink + s_blue + s_red + s_green
        total_bet_amount = main_bet_amount + side_bet_amount
        main_bet_win = False
        side_bet_win = False
        side_bet_set = False
        if not self._game_on.get():
            Logger.debug(f'Game not active yet.', TAG)
            revert(f'Game not active yet.')
        if not (0 <= yellow <= main_bet_limit and 0 <= white <= main_bet_limit and
                0 <= pink <= main_bet_limit and 0 <= blue <= main_bet_limit and
                0 <= red <= main_bet_limit and 0 <= green <= main_bet_limit):
            Logger.debug(f'Bets placed out of range numbers', TAG)
            revert(f'Invalid main bet. Choose a number between 0 to 100')
        if not (0 <= s_yellow <= side_bet_limit and 0 <= s_white <= side_bet_limit and
                0 <= s_pink <= side_bet_limit and 0 <= s_blue <= side_bet_limit and
                0 <= s_red <= side_bet_limit and 0 <= s_green <= side_bet_limit):
            Logger.debug(f'Bets placed out of range numbers', TAG)
            revert(f'Invalid side bet. Choose a number between 0 to 10')
        if not (BET_MIN <= main_bet_amount <= main_bet_limit):
            Logger.debug(f'Betting amount {main_bet_amount} out of range.', TAG)
            revert(f'Main bet amount {main_bet_amount} out of range ({BET_MIN} ,{main_bet_limit}).')
        if not main_bet_amount == (self.msg.value - side_bet_amount):
            Logger.debug(f'Invalid bet. Main bet value must equal Main bet amount', TAG)
            revert(f'Main Bet amount {main_bet_amount} doesnt equal Main bet Value {self.msg.value - side_bet_amount} ')
        if not side_bet_amount == (self.msg.value - main_bet_amount):
            Logger.debug(f'Invalid bet. Side bet value must equal Side bet amount', TAG)
            revert(f'Side Bet amount {side_bet_amount} doesnt equal Side bet Value {self.msg.value - main_bet_amount} ')
        if (side_bet_type == '' and side_bet_amount != 0) or (side_bet_type != '' and side_bet_amount == 0):
            Logger.debug(f'should set both side bet type as well as side bet amount', TAG)
            revert(f'should set both side bet type as well as side bet amount')
        if side_bet_type != '' and side_bet_amount != 0:
            side_bet_set = True
            if side_bet_type not in SIDE_BET_TYPES:
                Logger.debug(f'Invalid side bet type', TAG)
                revert(f'Invalid side bet type.')
            if not (BET_MIN <= side_bet_amount <= side_bet_limit):
                Logger.debug(f'Betting amount {side_bet_amount} out of range.', TAG)
                revert(f'Side bet amount {side_bet_amount} out of range ({BET_MIN} ,{side_bet_limit}).')

        # execute rolls
        colors = ['Y', 'W', 'P', 'B', 'R', 'G']
        results = []
        spin = self.get_random(user_seed)
        num1 = spin
        num2 = spin // 1000
        num3 = num2 // 1000
        color1 = num1 % 6
        color2 = num2 % 6
        color3 = num3 % 6
        results.append(colors[color1])
        results.append(colors[color2])
        results.append(colors[color3])
        Logger.debug(f'Results were {results}.', TAG)
        self.RollsResult(str(results))

        # check for main bet win
        user_main = {'Y': yellow, 'W': white, 'P': pink, 'B': blue, 'R': red, 'G': green}
        m_payout = 0
        for j in user_main:
            color_count = 0
            for k in results:
                if j == k:
                    color_count += 1
            if color_count != 0:
                m_payout += user_main[j] + (color_count * user_main[j])
        if m_payout > 0:
            main_bet_win = True
        else:
            main_bet_win = False

        # check for side bet win
        user_side = {'Y': s_yellow, 'W': s_white, 'P': s_pink, 'B': s_blue, 'R': s_red, 'G': s_green}
        s_payout = 0
        if side_bet_set:
            if side_bet_type == SIDE_BET_TYPES[0]:  # specific double
                for m in user_side:
                    if user_side[m] == 0:
                        continue
                    else:
                        color_count = 0
                        for k in results:
                            if m == k:
                                color_count += 1
                        if color_count == 2 or color_count == 3:
                            s_payout += user_side[m] + (user_side[m] * 10)
                            side_bet_win = True
            elif side_bet_type == SIDE_BET_TYPES[1]:  # specific triple
                for n in user_side:
                    if user_side[n] == 0:
                        continue
                    else:
                        color_count = 0
                        for k in results:
                            if n == k:
                                color_count += 1
                        if color_count == 3:
                            s_payout += user_side[n] + (user_side[n] * 180)
                            side_bet_win = True
            elif side_bet_type == SIDE_BET_TYPES[2]:  # any triple
                if results[0] == results[1] == results[2]:
                    total_user_side_bet_amount = 0
                    for o in user_side:
                        total_user_side_bet_amount += user_side[o]
                    s_payout += total_user_side_bet_amount + (total_user_side_bet_amount * 30)
                    side_bet_win = True
            else:
                side_bet_win = False

        # payout
        payout = m_payout + s_payout
        if payout == 0:
            self._take_wager(total_bet_amount)
        else:
            self._take_wager_and_request_payout(total_bet_amount, payout)
        self.TotalPayoutAmount(str(payout))
        self.MainBet(str(main_bet_win), str(m_payout))
        self.SideBet(str(side_bet_win), str(s_payout))

    def _take_wager(self, _wager: int):
        try:
            self.icx.transfer(self._roulette_score.get(), _wager)
            self.FundTransfer(self._roulette_score.get(), _wager, "Sending icx to roulette")
            roulette_score = self.create_interface_score(self._roulette_score.get(), RouletteInterface)
            roulette_score.take_wager(_wager)
        except BaseException as e:
            revert('Network problem. Winnings not sent. Will try again. '
                   f'Exception: {e}')

    def _take_wager_and_request_payout(self, _wager: int, _payout: int):
        try:
            self.icx.transfer(self._roulette_score.get(), _wager)
            self.FundTransfer(self._roulette_score.get(), _wager, "Sending icx to roulette")
            roulette_score = self.create_interface_score(self._roulette_score.get(), RouletteInterface)
            roulette_score.take_wager(_wager)
            roulette_score.wager_payout(_payout)
        except BaseException as e:
            revert('Network problem. Winnings not sent. Will try again. '
                   f'Exception: {e}')

    @payable
    def fallback(self):
        pass