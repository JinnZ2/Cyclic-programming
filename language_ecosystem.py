# language_ecosystem.py — cross-language repurposing to avoid lock-in.
# CC0. stdlib + repurpose_controller.py. phone-buildable.
#
# Models programming languages as nodes.  When one language community
# is in surplus, its excess maintenance capacity can be directed to
# help a struggling language (via transpilers, bindings, shared tooling).
# This prevents the "cheaper to let it die" threshold.

from harm import System, Node, Coupling
import repurpose_controller as rc

def language_system(cross_lang=True):
    """
    Nodes:
      Py  : Python   — draw 2.0, regen 3.0  (surplus, large community)
      Ru  : Rust     — draw 2.5, regen 2.2  (growing, slightly stressed)
      Js  : JavaScript—draw 2.8, regen 2.5  (large but churn hurts)
      Cob : COBOL    — draw 1.8, regen 1.0  (legacy, deficit)

    Couplings: internal to the language — each language's own churn
    slightly erodes the others (because developers may abandon one for
    another).  But cross-language repurpose actions counteract this.

    If cross_lang=True, the controller will use surplus from Py to
    heal Cob, and from Ru to heal Js (as an example policy).
    """
    nodes = {
        "Py":  Node(draw=2.0, regen=3.0),
        "Ru":  Node(draw=2.5, regen=2.2),
        "Js":  Node(draw=2.8, regen=2.5),
        "Cob": Node(draw=1.8, regen=1.0),
    }
    couplings = [
        # Internal churn: a struggling language pulls resources from others
        Coupling("Cob", "Py", transfer=0.3, sensitivity=0.2),  # COBOL decline demoralises Python?
        Coupling("Js", "Ru", transfer=0.2, sensitivity=0.3),   # JS churn distracts Rust
    ]
    return System(nodes, couplings), nodes


def cross_language_controller(t, system, reserve):
    """
    Repurpose surplus from a healthy language to a deficit one.
    Policy: if Python has surplus (regen > draw) and COBOL is in deficit,
    transfer 0.5 capacity from Python to COBOL.  If Rust has surplus and
    JavaScript is in deficit, transfer 0.3 from Rust to JS.
    """
    actions = []
    fields = system.nodes
    # Python -> COBOL
    if fields["Py"].regen > fields["Py"].draw and fields["Cob"].regen <= fields["Cob"].draw:
        if reserve.value >= 0.5:
            actions.append(("Cob", 0.5))
            # Simulate Python losing a little regen as cost of translation work
            fields["Py"].regen -= 0.1  # maintenance overhead
    # Rust -> JavaScript
    if fields["Ru"].regen > fields["Ru"].draw and fields["Js"].regen <= fields["Js"].draw:
        if reserve.value >= 0.3:
            actions.append(("Js", 0.3))
            fields["Ru"].regen -= 0.05
    return actions


def run_scenario(cross_lang):
    sys, _ = language_system(cross_lang)
    reserve = rc.RepurposeReserve(initial=5.0, decay_rate=0.02)
    controller = cross_language_controller if cross_lang else None
    trace, locked, _ = rc.run_with_repurposing(
        sys, ticks=30, erosion=1.0, regen_rate=0.05,
        repurpose_reserve=reserve, controller=controller
    )
    return trace, locked

if __name__ == "__main__":
    print("=== Without cross-language repurposing ===")
    trace_no, lock_no = run_scenario(cross_lang=False)
    print(f"DOF start: {trace_no[0]['dof']}, end: {trace_no[-1]['dof']}, locked at: {lock_no}")

    print("\n=== With cross-language repurposing (no waste) ===")
    trace_yes, lock_yes = run_scenario(cross_lang=True)
    print(f"DOF start: {trace_yes[0]['dof']}, end: {trace_yes[-1]['dof']}, locked at: {lock_yes}")

    # Show the second-order tell
    if lock_yes is None:
        print("§1 threshold NOT crossed — ecosystem remains reversible.")
    else:
        L = trace_yes[lock_yes]
        print(f"Locked at t={lock_yes}: reversal={L['reversal']}, continuation={L['continuation']}")
