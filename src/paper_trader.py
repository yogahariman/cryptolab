class PaperTrader:
    def __init__(self, database, strategy):
        self.database = database
        self.strategy = strategy

    def on_signal(self, symbol: str, price: float, buy: bool) -> None:
        if buy and not self.database.get_open_position(symbol):
            target = price * (1 + self.strategy["take_profit_percent"] / 100)
            self.database.open_paper_position(
                symbol, price, self.strategy["levels"][0]["order_amount_usdt"], target
            )
            print(f"PAPER BUY level 0: price={price:.2f}, target={target:.2f}")

    def update(self, symbol: str, price: float) -> None:
        position = self.database.get_open_position(symbol)
        if not position:
            return

        if price >= position[8]:
            self.database.close_paper_position(position, price)
            print(f"PAPER SELL: price={price:.2f}, target reached")
            return

        next_level = position[7] + 1
        levels = self.strategy["levels"]
        if next_level >= len(levels):
            return
        level = levels[next_level]
        spacing = level["spacing_percent"]
        trigger = position[6] * (1 - spacing / 100)
        if price <= trigger:
            new_cost = position[4] + level["order_amount_usdt"]
            new_quantity = position[3] + level["order_amount_usdt"] / price
            target = (new_cost / new_quantity) * (1 + self.strategy["take_profit_percent"] / 100)
            self.database.add_paper_level(position, symbol, next_level, price, level["order_amount_usdt"], target)
            print(f"PAPER BUY level {next_level}: price={price:.2f}, target={target:.2f}")

