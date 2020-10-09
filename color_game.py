from iconservice import *

TAG = 'Colors'
DEBUG = True
BET_MIN = 0.1
SIDE_BET_TYPES = ["specific_double", "specific_triple", "any_triple"]
SIDE_BET_MULTIPLIERS = [10, 180, 30]

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
        if DEBUG is True:
            Logger.debug(f'In __init__.', TAG)
            Logger.debug(f'owner is {self.owner}.', TAG)
        self._game_on = VarDB(self._GAME_ON, db, value_type=bool)
        self._roulette_score = VarDB(self._ROULETTE_SCORE, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()
        self._game_on.set(False)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=1)
    def RollsResult(self, results: str):
        pass

    @eventlog(indexed=1)
    def BetPayouts(self, main_bet_win: str):
        pass

    @eventlog(indexed=1)
    def SidePayouts(self, side_bet_win: str):
        pass

    @eventlog(indexed=1)
    def PayoutAmount(self, payout: str):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, recipient: Address, amount: int, note: str):
        pass

    @external(readonly=True)
    def get_score_owner(self) -> Address:
        """
        A function to return the owner of this score.
        :return: Owner address of this score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self.owner

    @external
    def set_roulette_score(self, _score: Address) -> None:
        """
        Sets the roulette score address. The function can only be invoked by score owner.
        :param _score: Score address of the roulette
        :type _score: :class:`iconservice.base.address.Address`
        """
        if self.msg.sender == self.owner:
            self._roulette_score.set(_score)

    @external(readonly=True)
    def get_roulette_score(self) -> Address:
        """
        Returns the roulette score address.
        :return: Address of the roulette score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self._roulette_score.get()

    @external
    def game_on(self) -> None:
        """
        Set the status of game as on. Only the owner of the game can call this method. Owner must have set the
        roulette score before changing the game status as on.
        """
        if self.msg.sender != self.owner:
            revert('Only the owner can call the game_on method')
        if not self._game_on.get() and self._roulette_score.get() is not None:
            self._game_on.set(True)

    @external
    def game_off(self) -> None:
        """
        Set the status of game as off. Only the owner of the game can call this method.
        """
        if self.msg.sender != self.owner:
            revert('Only the owner can call the game_on method')
        if self._game_on.get():
            self._game_on.set(False)

    @external(readonly=True)
    def get_game_on(self) -> bool:
        """
        Returns the current game status
        :return: Current game status
        :rtype: bool
        """
        return self._game_on.get()

    @external
    def untether(self) -> None:
        """
        A function to redefine the value of  self.owner once it is possible .
        To  be included through an update if it is added to ICONSERVICE
        Sets the value of self.owner to the score holding the game treasury
        """
        if self.msg.sender != self.owner:
            revert('Only the owner can call the untether method ')
        pass

    def get_random(self, user_seed: str = '', rolls: int = 0) -> float:
        Logger.debug(f'Entered get_random.', TAG)
        if rolls == 0:
            roll1 = self.tx.hash[2:22]
            seed = (str(bytes.hex(roll1)) + str(self.now()) + user_seed)
            spin = (int.from_bytes(sha3_256(seed.encode()), "big") % 6)
            Logger.debug(f'Result of the spin was {spin}.', TAG)
        elif rolls == 1:
            roll2 = self.tx.hash[23:44]
            seed = (str(bytes.hex(roll2)) + str(self.now()) + user_seed)
            spin = (int.from_bytes(sha3_256(seed.encode()), "big") % 6)
            Logger.debug(f'Result of the spin was {spin}.', TAG)
        elif rolls == 2:
            roll3 = self.tx.hash[45:66]
            seed = (str(bytes.hex(roll3)) + str(self.now()) + user_seed)
            spin = (int.from_bytes(sha3_256(seed.encode()), "big") % 6)
            Logger.debug(f'Result of the spin was {spin}.', TAG)
        return spin

    @payable
    @external
    def call_bet(self, yellow: str, white: str, pink: str, blue: str, red: str, green: str, s_yellow: str, s_white: str,
                 s_pink: str, s_blue: str, s_red: str, s_green: str, side_bet_type: str = '', user_seed: str = '') -> None:
        return self.bet(yellow, white, pink, blue, red, green, s_yellow, s_white, s_pink, s_blue, s_red, s_green,
                          side_bet_type, user_seed)

    def bet(self, yellow: str, white: str, pink: str, blue: str, red: str, green: str,
            s_yellow: str, s_white: str, s_pink: str, s_blue: str, s_red: str, s_green: str,
            side_bet_type: str = '', user_seed: str = '') -> None:
        yellow = float(yellow)
        white = float(white)
        pink = float(pink)
        blue = float(blue)
        red = float(red)
        green = float(green)
        s_yellow = float(s_yellow)
        s_white = float(s_white)
        s_pink = float(s_pink)
        s_blue = float(s_blue)
        s_red = float(s_red)
        s_green = float(s_green)
        main_bet_payout = 0
        side_bet_payout = 0
        payout = side_bet_payout + main_bet_payout
        side_bet_win = False
        side_bet_set = False
        roulette_score = self.create_interface_score(self._roulette_score.get(), RouletteInterface)
        _treasury_min = roulette_score.get_treasury_min()
        self.icx.transfer(self._roulette_score.get(), self.msg.value)
        self.FundTransfer(self._roulette_score.get(), self.msg.value, "Sending icx to Roulette")
        roulette_score.take_wager(self.msg.value)
        if not self._game_on.get():
            Logger.debug(f'Game not active yet.', TAG)
            revert(f'Game not active yet.')
        if not (0 <= yellow <= 100 and 0 <= white <= 100 and 0 <= pink <= 100 and 0 <= blue <= 100 and
                0 <= red <= 100 and 0 <= green <= 100):
            Logger.debug(f'Bets placed out of range numbers', TAG)
            revert(f'Invalid bet. Choose a number between 0 to 100')
        if not (0 <= yellow + white + pink + blue + red + green <= 100):
            Logger.debug(f'Maximum bet exceeded', TAG)
            revert(f'Maximum bet exceeded. Your total bet should be between 0 and 100')
        side_bet_amount = s_yellow + s_white + s_pink + s_blue + s_red + s_green
        if (side_bet_type == '' and side_bet_amount != 0) or (side_bet_type != '' and side_bet_amount == 0):
            Logger.debug(f'should set both side bet type as well as side bet amount', TAG)
            revert(f'should set both side bet type as well as side bet amount')
        if side_bet_amount < 0:
            revert(f'Bet amount cannot be negative')
        if side_bet_type != '' and side_bet_amount != 0:
            side_bet_set = True
            if side_bet_type not in SIDE_BET_TYPES:
                Logger.debug(f'Invalid side bet type', TAG)
                revert(f'Invalid side bet type.')
            side_bet_limit = 10
            if side_bet_amount < BET_MIN or side_bet_amount > side_bet_limit:
                Logger.debug(f'Betting amount {side_bet_amount} out of range.', TAG)
                revert(f'Betting amount {side_bet_amount} out of range ({BET_MIN} ,{side_bet_limit}).')
        main_bet_amount = yellow + white + pink + blue + red + green
        if main_bet_amount == 0:
            Logger.debug(f'No main bet amount provided', TAG)
            revert(f'No main bet amount provided')
        main_bet_limit = 100
        if main_bet_amount < BET_MIN or main_bet_amount > main_bet_limit:
            Logger.debug(f'Betting amount {main_bet_amount} out of range.', TAG)
            revert(f'Main Bet amount {main_bet_amount} out of range {BET_MIN},{main_bet_limit} ')

        # execute rolls
        colors = ['Y', 'W', 'P', 'B', 'R', 'G']
        results = []
        rolls = 0
        while rolls < 3:
            spin = self.get_random(user_seed, rolls)
            winning_color = colors[spin]
            results.append(winning_color)
            Logger.debug(f'winning_color was {winning_color}.', TAG)
            rolls += 1
        self.RollsResult(str(results))

        # check for main bet win
        user_main = {'Y': yellow, 'W': white, 'P': pink, 'B': blue, 'R': red, 'G': green}
        m_payout = 0
        for j in user_main:
            color_count = 0
            for k in results:
                if j == k:
                    color_count += 1
            if color_count == 1:
                m_payout += user_main[j] + (user_main[j] * 1)
            elif color_count == 2:
                m_payout += user_main[j] + (user_main[j] * 2)
            elif color_count == 3:
                m_payout += user_main[j] + (user_main[j] * 3)
        if m_payout > 0:
            main_bet_win = True
        else:
            main_bet_win = False

        # check for side bet win
        user_side = {'Y': s_yellow, 'W': s_white, 'P': s_pink, 'B': s_blue, 'R': s_red, 'G': s_green}
        s_payout = 0
        if side_bet_type != '' and s_yellow != 0 and s_white != 0 and s_pink != 0 and s_blue != 0 and s_red != 0 and s_green != 0:
            side_bet_set = True
        if side_bet_set:
            if side_bet_type == SIDE_BET_TYPES[0]:  # specific double
                for m in user_side:
                    color_count = 0
                    for k in results:
                        if m == k:
                            color_count += 1
                    if color_count == 2 or color_count == 3:
                        s_payout += user_side[m] + (user_side[m] * 10)
                        side_bet_win = True
            elif side_bet_type == SIDE_BET_TYPES[1]:  # specific triple
                for n in user_side:
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
        main_bet_payout += m_payout
        side_bet_payout += s_payout
        payout = main_bet_payout + side_bet_payout
        self.PayoutAmount(str(payout))
        self.BetPayouts(str(main_bet_win))
        self.SidePayouts(str(side_bet_win))
        if main_bet_win or side_bet_win:
            Logger.debug(f'Amount owed to winner: {payout}', TAG)
            try:
                Logger.debug(f'Trying to send to ({self.tx.origin}): {payout}.', TAG)
                roulette_score.wager_payout(payout)
                Logger.debug(f'Sent winner ({self.tx.origin}) {payout}.', TAG)
            except BaseException as e:
                Logger.debug(f'Send failed. Exception: {e}', TAG)
                revert('Network problem. Winnings not sent. Returning funds.')
        else:
            Logger.debug(f'Player lost. ICX retained in treasury.', TAG)

    @payable
    def fallback(self):
        pass