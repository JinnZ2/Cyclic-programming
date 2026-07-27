# language_ecosystem_with_table.py — cross-language repurposing with real data.
# CC0. stdlib + repurpose_controller.py + language_translation_table.py.

from harm import System, Node, Coupling
import repurpose_controller as rc
from language_translation_table import best_donor_for

def language_system():
    nodes = {
        "Python":     Node(draw=2.0, regen=3.0),
        "Rust":       Node(draw=2.5, regen=2.2),
        "JavaScript": Node(draw=2.8, regen=2.5),
        "COBOL":      Node(draw=1.8, regen=1.0),
    }
    couplings = [
        Coupling("COBOL", "Python", transfer=0.3, sensitivity=0.2),
        Coupling("JavaScript", "Rust", transfer=0.2, sensitivity=0.3),
    ]
    return System(nodes, couplings), nodes

def translation_table_controller(t, system, reserve):
    """
    1. Find languages in deficit (regen <= draw).
    2. For each, find the best donor with surplus (regen > draw).
    3. Transfer a fraction of the donor's surplus to the deficit language,
       consuming reserve proportional to translation cost.
    """
    actions = []
    fields = system.nodes
    # Identify surplus and deficit languages
    surplus = [name for name, nd in fields.items() if nd.regen > nd.draw]
    deficit = [name for name, nd in fields.items() if nd.regen <= nd.draw]

    for target in deficit:
        # Find best donor that isn't itself
        donors = [s for s in surplus if s != target]
        if not donors:
            continue
        best = best_donor_for(target, donors)
        if best is None:
            continue
        src, cost, effectiveness = best
        # Amount we're willing to transfer: 20% of donor's surplus, but no more than reserve
        donor_surplus = fields[src].regen - fields[src].draw
        transfer_amount = min(donor_surplus * 0.2, reserve.value / cost if cost > 0 else 1.0)
        if transfer_amount <= 0:
            continue
        # Cost to the reserve (translation effort)
        reserve_cost = transfer_amount * cost
        if reserve.value < reserve_cost:
            transfer_amount = reserve.value / cost
            reserve_cost = reserve.value
        # Apply: donor loses a little regen, target gains, reserve pays
        fields[src].regen -= transfer_amount * 0.1  # small maintenance hit
        actions.append((target, transfer_amount * effectiveness))
        reserve.value -= reserve_cost
    return actions

# Run comparison
def run_comparison():
    print("=== Without cross‑language repurposing ===")
    sys_no, _ = language_system()
    reserve_no = rc.RepurposeReserve(initial=5.0, decay_rate=0.02)
    trace_no, lock_no, _ = rc.run_with_repurposing(
        sys_no, ticks=30, erosion=1.0, regen_rate=0.05,
        repurpose_reserve=reserve_no, controller=None
    )
    print(f"DOF: {trace_no[0]['dof']} → {trace_no[-1]['dof']}, locked at: {lock_no}")

    print("\n=== With translation‑table‑driven repurposing ===")
    sys_yes, _ = language_system()
    reserve_yes = rc.RepurposeReserve(initial=5.0, decay_rate=0.02)
    trace_yes, lock_yes, _ = rc.run_with_repurposing(
        sys_yes, ticks=30, erosion=1.0, regen_rate=0.05,
        repurpose_reserve=reserve_yes, controller=translation_table_controller
    )
    print(f"DOF: {trace_yes[0]['dof']} → {trace_yes[-1]['dof']}, locked at: {lock_yes}")
    if lock_yes is None:
        print("§1 threshold NOT crossed — ecosystem remains reversible.")
    else:
        L = trace_yes[lock_yes]
        print(f"Locked at t={lock_yes}: reversal={L['reversal']}, continuation={L['continuation']}")

if __name__ == "__main__":
    run_comparison()
