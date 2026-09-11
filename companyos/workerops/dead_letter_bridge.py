class DeadLetterBridge:
    def move(self, dead_letter_queue, job, reason):
        return dead_letter_queue.add(job, reason)
