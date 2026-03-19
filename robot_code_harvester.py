class FarmerBot(HarvesterRobot):
    def work(self):
        for i in range(5):
            self.harvest()
            self.move(1, 0)
       