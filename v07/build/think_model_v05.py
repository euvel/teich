"""Teich v0.5 — its cheap, order-blind model of its own thinking (frozen genome constants; law L-CL: no geometry,
no body — one multiply-add per thought). Coefficients: exact single-thought effects at the rest shape (design 10-21)."""
L0 = float.fromhex("0x1.0c0616dae6668p+1")           # the thinking handle's rest core length
A = [float.fromhex(h) for h in ("-0x1.994c2b0ba6ad0p-3", "-0x1.8dd1cf693a8a0p-2", "-0x1.fabef0478fc08p-2",
     "-0x1.a07a97f5371dcp-2", "-0x1.d0d757a270cb0p-4", "0x1.5cd00220c4f80p-4", "0x1.461c7fd6f9620p-2",
     "0x1.715c75e538fd0p-2", "-0x1.d56d2b6e3d2e0p-4")]
TOL = 0.02                                             # a prediction "holds" within 2% of the reading


def predict(thoughts):
    """Order-blind: the sum of each thought's own effect."""
    return L0 + sum(A[r] for r in thoughts)


def holds(predicted, read):
    return abs(read / predicted - 1.0) <= TOL
