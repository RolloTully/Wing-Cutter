for x in range(1000,1,-1):
        print(x)
        x=x/10
        #self.points = array([[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1],[0.5,0.5,0.5]])
        self.points = self.points - self.points.min(axis=0)
        self.points = self.points/self.points.max(axis=0)
        self.points +=[-0.5,-0.5,x]

        self.ders = self.points[:]/self.points[:,2].reshape(self.points.shape[0],1)
        print(self.ders)
        self.projection  = self.ders[:,0:2]*array([200,200])
        print(self.projection[:,0].max(axis=0))
        print(self.projection[:,1].max(axis=0))
        print(self.projection[:,0].min(axis=0))
        print(self.projection[:,1].min(axis=0))
        self.img = zeros((200,200,3))
        for self.pix in self.projection:
            self.img[int(self.pix[0]),int(self.pix[1])] = [255,255,255]
        print(self.img)
        cv2.imshow("projection",self.img)
        cv2.waitKey(10)
