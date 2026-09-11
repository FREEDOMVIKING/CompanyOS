class RollbackPolicy:
    def evaluate(self, deploy_result, postdeploy):
        failed = not bool(deploy_result.get("success")) or not bool(postdeploy.get("passed"))
        return {
            "rollback_required": failed,
            "action": "rollback_to_last_known_good" if failed else "keep_release"
        }
