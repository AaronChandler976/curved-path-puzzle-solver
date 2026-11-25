"""Run 04: the pre-registered tail-aware term (src/disasm/models/tail_loss.py)."""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_neuralsort_is_permutation_at_small_tau():
    from disasm.models.tail_loss import neuralsort
    s = torch.tensor([0.3, -1.0, 2.0, 0.9])
    P = neuralsort(s, 1e-3)
    assert torch.allclose(P.sum(1), torch.ones(4))
    assert torch.equal(P.argmax(1), torch.argsort(s, descending=True))


def test_soft_cost_matches_hard_cost_and_has_gradient():
    from disasm.models.tail_loss import hard_replay_cost, soft_replay_cost
    torch.manual_seed(0)
    for _ in range(20):
        n = int(torch.randint(2, 9, (1,)))
        s = torch.randn(n, requires_grad=True) * 3
        y = torch.rand(n) < 0.6
        y[0] = True
        t = torch.where(y, torch.rand(n) * 3, torch.full((n,), 30.0))
        c = soft_replay_cost(s, y, t, tau=1e-3)
        assert abs(float(c) - hard_replay_cost(s.detach(), y, t)) < 1e-2
    s = torch.tensor([1.0, 0.0], requires_grad=True)       # unsolved part ranked first: cost 30 + 1
    c = soft_replay_cost(s, torch.tensor([False, True]), torch.tensor([30.0, 1.0]), tau=0.5)
    c.backward()
    assert s.grad[0] > 0 and s.grad[1] < 0                  # descending the loss swaps the order


def test_grouped_tail_term_equals_loop():
    from disasm.models.tail_loss import tail_term, tail_term_grouped
    torch.manual_seed(1)
    sizes = [3, 5, 3, 8, 2, 5, 12, 3]
    batch = torch.cat([torch.full((n,), i) for i, n in enumerate(sizes)])
    perm = torch.randperm(len(batch))            # nodes need not be contiguous per state
    batch = batch[perm]
    N = len(batch)
    s = (torch.randn(N) * 2).requires_grad_(True)
    y = torch.rand(N) < 0.5
    y[batch == 4] = False                        # a state with no success is excluded
    t = torch.where(y, torch.rand(N) * 3, torch.full((N,), 31.0))
    a = tail_term(s, y, t, batch, 30.0, 0.1)
    ga, = torch.autograd.grad(a, s)
    b = tail_term_grouped(s, y, t, batch, 30.0, 0.1)
    gb, = torch.autograd.grad(b, s)
    assert torch.allclose(a, b, atol=1e-6) and torch.allclose(ga, gb, atol=1e-5)   # float32 rounding of the 12x12 sort
