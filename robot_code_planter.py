class FarmerBot(PlanterRobot):
    def work(self):
        for i in range(5):
            self.plant('wheat')
            self.move(1, 0)