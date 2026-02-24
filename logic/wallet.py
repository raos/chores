from db.queries.chore_instances import (
    get_instance,
    transition_to_approved,
    transition_to_pending_approval,
    reset_to_pending,
)
from logic.allowance import credit_fixed_and_screen_time


def mark_done_by_child(instance_id: int) -> bool:
    return transition_to_pending_approval(instance_id)


def approve_by_parent(instance_id: int) -> bool:
    success = transition_to_approved(instance_id)
    if success:
        instance = get_instance(instance_id)
        if instance:
            credit_fixed_and_screen_time(instance)
    return success


def reset_chore(instance_id: int) -> bool:
    return reset_to_pending(instance_id)
