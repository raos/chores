from db.queries.chore_instances import get_approved_weighted_instances_for_week
from db.queries.wallets import credit_wallet, is_week_finalized, save_week_snapshot
from db.queries.children import get_child
import json


def credit_fixed_and_screen_time(instance) -> None:
    child_id = instance["assigned_to"]
    instance_id = instance["id"]
    allowance_type = instance["allowance_type"]

    if allowance_type in ("fixed", "both") and instance["fixed_amount"]:
        credit_wallet(
            child_id=child_id,
            chore_instance_id=instance_id,
            transaction_type="monetary",
            amount=instance["fixed_amount"],
            note=f"Fixed allowance for: {instance['title']}",
        )

    if instance["screen_time_hours"] and instance["screen_time_hours"] > 0:
        credit_wallet(
            child_id=child_id,
            chore_instance_id=instance_id,
            transaction_type="screen_time",
            amount=instance["screen_time_hours"],
            note=f"Screen time for: {instance['title']}",
        )


def finalize_week(child_id: int, week_start: str, week_end: str) -> dict:
    if is_week_finalized(child_id, week_start):
        return {"status": "already_finalized"}

    child = get_child(child_id)
    if not child:
        return {"status": "child_not_found"}

    budget = child["weekly_allowance_budget"]
    instances = get_approved_weighted_instances_for_week(child_id, week_start, week_end)

    if not instances:
        return {"status": "no_weighted_chores"}

    total_weight = sum(i["chore_weight"] for i in instances if i["chore_weight"])
    if total_weight == 0:
        return {"status": "zero_weight"}

    total_payout = 0.0
    calculation = []
    for inst in instances:
        weight = inst["chore_weight"] or 0
        payout = (weight / total_weight) * budget
        total_payout += payout
        calculation.append({
            "instance_id": inst["id"],
            "chore_title": inst["title"],
            "weight": weight,
            "payout": round(payout, 2),
        })
        credit_wallet(
            child_id=child_id,
            chore_instance_id=inst["id"],
            transaction_type="monetary",
            amount=round(payout, 2),
            note=f"Weighted allowance for: {inst['title']}",
        )

    save_week_snapshot(
        child_id=child_id,
        week_start=week_start,
        total_payout=round(total_payout, 2),
        calculation_json=json.dumps(calculation),
    )
    return {
        "status": "finalized",
        "total_payout": round(total_payout, 2),
        "details": calculation,
    }
