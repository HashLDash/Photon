
def xyz(int a, float b, str c, int d = [], float e = [], str f = []):
    print("{a} | {b} | {c} | {d} | {e} | {f}")

def test(func callback):
    callback(1, 2.0, "Matheus", [1, 2], [1.0, 2.0], ["PHO", "TON"])

test(xyz)
