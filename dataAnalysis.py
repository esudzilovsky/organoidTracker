# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 19:26:27 2017

@author: Ed
"""

import csv;
import numpy as np;
import scipy;
import scipy.optimize;
    
"""
    Gives the distance between 2 points
"""
def distance(pt1,pt2):
    return ((pt1[0]-pt2[0])**2+(pt1[1]-pt2[1])**2)**0.5;

def getMinMaxPoints(points):
    maxx = points[0][0];
    minx = points[0][0];
    maxy = points[0][1];
    miny = points[0][1];
    for pt in points:
        if pt[0]>maxx:
            maxx = pt[0];
        if pt[0]<minx:
            minx = pt[0];
        if pt[1]>maxy:
            maxy = pt[1];
        if pt[1]<miny:
            miny = pt[1];
    return minx,maxx,miny,maxy;
    
"""
    Gets the difference between every two items in x at dt interval
"""

def diff(x,dt):
    xout = [];
    #for init in range(0,len(x)):
    #    for i in range(dt+init,len(x),dt):
    #        xout.append(x[i]-x[i-dt]);
    for i in range(0,len(x)-dt):
        xout.append(x[i+dt]-x[i]);    
    return xout;

class diodeAnalysis(object):
    def __init__(self):
        self.x = None;
        self.y = None;
        self.t = None;
        self.filename = None;
        
    """
       Reads the measurements for a single particle from a *.csv file and returns them
    """       
    def ReadFromCSV(self,filename):
        # For all files with the extension 'csv' in this folder
        #for csvfile in glob.glob(os.path.join('.', '*.csv')):
        
        print("Reading CSV file: ",filename);    
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|');
            x=[]; dx=[]; y=[]; dy=[]; t=[]; dt=[];        
            for row in reader:
                if row[0]=='x': #header
                    continue;
                if len(row)==7:
                    laserT = float(row[6]);
                x.append(float(row[0]));
                dx.append(float(row[1]));
                y.append(float(row[2]));
                dy.append(float(row[3]));
                t.append(float(row[4]));
                dt.append(float(row[5]));
            return x,dx,y,dy,t,dt,laserT;
            
    def saveAreaToCVS(self,t,a,windowSize):
        csv_filename = self.filename+"-"+str(windowSize)+"-area.csv";
        print('Writing to [area,t] CSV file: ',csv_filename,' ...');
        with open(csv_filename, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',\
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n');
            writer.writerow(['t','area']);      
            #writer.writerow([str(t[0]),str(a[0]),str(dt)]);
            for i in range(0,len(t)):
                writer.writerow([str(t[i]),str(a[i])]);
            print('Writing done!');
            
    def savePositionToCVS(self,t,r):
        csv_filename = self.filename+"-position.csv";
        print('Writing to [r,t] CSV file: ',csv_filename,' ...');
        with open(csv_filename, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',\
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n');
            writer.writerow(['t','r']);      
            for i in range(0,len(t)):
                writer.writerow([str(t[i]),str(r[i])]);
            print('Writing done!');
            
    def saveVelocityToCVS(self,t,v):    
        csv_filename = self.filename+"-velocity.csv";
        print('Writing to [v,t] CSV file: ',csv_filename,' ...');
        with open(csv_filename, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',\
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n');
            writer.writerow(['t','v']);      
            for i in range(0,len(t)):
                writer.writerow([str(t[i]),str(v[i])]);
            print('Writing done!');
            
    def saveMSDToCVS(self,csv_filename,dt,MSD,MSD_error):    
        print('Writing to [dt,MSD,dMSD] CSV file: ',csv_filename,' ...');
        with open(csv_filename, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',\
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n');
            writer.writerow(['dt','MSD','dMSD']);      
            for i in range(0,len(dt)):
                writer.writerow([str(dt[i]),str(MSD[i]),str(MSD_error[i])]);
            print('Writing done!');
            
    def saveRollingAlphaToCVS(self,alpha,t,dt):
        csv_filename = self.filename+"-"+str(dt)+"-rollingAlpha.csv";
        print('Writing to [alpha,t] CSV file: ',csv_filename,' ...');
        with open(csv_filename, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',\
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n');
            writer.writerow(['t','alpha','dt']);      
            writer.writerow([str(t[0]),str(alpha[0]),str(dt)]);
            for i in range(1,len(t)):
                writer.writerow([str(t[i]),str(alpha[i])]);
            print('Writing done!');
            
    def loadFileForAnalysis(self,csvFile,pixelSize,plt,drift=[0,0],skippoints=10,factor=1.5):
        x,dx,y,dy,t,dt,laserT = self.ReadFromCSV(csvFile);
        self.x = ((np.array(x[skippoints:])-drift[0])*pixelSize)*1/factor;
        self.y = ((np.array(y[skippoints:])-drift[1])*pixelSize)*1/factor;
        self.t = np.array(t[skippoints:]);
        self.filename = csvFile;
        self.pixelSize = pixelSize;
        self.plt = plt;
        
    def getX(self):
        return self.x;
    
    def getY(self):
        return self.y;
    
    def getT(self):
        return self.t;
        
    def smooth7PointWeightedAverage(self,data,t):    
        outData = [];
        outTime = [];
        for i in range(3,len(data)-3):
            outData.append(data[i-3]*0.1+data[i-2]*0.1+data[i-1]*0.20\
                    +data[i]*0.20\
                    +data[i+1]*0.20+data[i+2]*0.1+data[i+3]*0.1);
            outTime.append(t[i]);
        return np.array(outData), np.array(outTime);
    
    """
        Returns velocity series for (x,y,t) points
        The velocity is calculted using points at 10 time (frame) intervals.
    """
    def getVelocity(self):
        x,y,t = self.x, self.y, self.t;
        vt = t+5;
        v = [];
        for i in range(5,len(x)-5):
            v.append(abs(distance([x[i-5],y[i-5]],[x[i+5],y[i+5]]))/10);
            #vvec.append(np.array([(x[i+5]-x[i-5])/10,(y[i+5]-y[i-5])/10]));
        return np.array(v),np.array(range(5,len(x)-5));
        
    """
        Returns the distance from initial point as a function of t.
    """
    def getDistance(self):
        x,y,t = self.x, self.y, self.t;
        rlist = np.array(x);
        for i in range(0,len(x)):
            r = distance([x[0],y[0]],[x[i],y[i]]);
            rlist[i] = r;
        return rlist,t;
        
    def getMovingArea(self,dt):
        x,y,t = self.x, self.y, self.t;

        tList = [];
        aList = [];
        add = int(dt/2);
    
        for k in range(add,len(x)-add):    
            points = [];
            for i in range(k-add,k+add):
                points.append([x[i],y[i]]);
            minx,maxx,miny,maxy = getMinMaxPoints(points)
            area = (maxx-minx)*(maxy-miny);
            aList.append(area);
            tList.append(t[k]);
            
        a1, a1t = self.smooth7PointWeightedAverage(aList,tList);
        
        #plt.plot(tList[3:-3],a1);
        #plt.plot(tList,aList,'b');
        #plt.show();
        
        return a1,a1t;
        
    def getMSD(self,x,y):
        MDS_list = [];
        MDSerror_list = [];
        dt_list = [];
        for dt in range(1,len(x)):
            dx  = diff(x,dt);
            dy  = diff(y,dt);
            #dx = x[:dt]-x[0];
            #dy = y[:dt]-y[0];
            DS  = np.power(dx,2)+np.power(dy,2);
            MDSerror = np.std(DS);
            MDS = np.mean(DS);
            #if MDS<=MDSerror:
            #    MDS = 0;
            MDSerror_list.append(MDSerror);
            MDS_list.append(MDS);
            dt_list.append(dt);
            
        return MDS_list, MDSerror_list, dt_list
        nCutPoints = np.int(len(MDS_list)/10);
        return MDS_list[nCutPoints:-nCutPoints], MDSerror_list[nCutPoints:-nCutPoints], dt_list[nCutPoints:-nCutPoints];
        
    """
        Finds a fit for y = a[3]*(x**a[1]), returns the a array as well as the fit y.
    """
    
    def findMSDFit(self,xin,yin):
        pixelSize = self.pixelSize;
        x = np.array(xin);
        y = np.array(yin);
        
        func = lambda a,x: a[0]*(x**a[1]);
        ErrorFunc=lambda a,x,y: func(a,x)-y;
        
        fitP,success = scipy.optimize.leastsq(ErrorFunc,[(pixelSize**2),1.5],args=(x,y));
        return fitP,func(fitP,x);
        
        #func = lambda x,a: a[3]*((a[0]+x)**a[1])+a[2];
        func = lambda x,a: a[3]*(x**a[1]);    
        
        mina = [0,0,np.min(y),(pixelSize**2)*0];
        maxa = [np.min(x),3,np.max(y),(pixelSize**2)];
        #mina[3] = np.power(np.e,-8.63964)*0.9*(pixelSize**2);
        #maxa[3] = np.power(np.e,-8.63964)*1.1*(pixelSize**2);          
        
        # Loop parameters
        cura = mina;  
        dmin = np.sum((func(x,cura)-y)**2);
        aForMinD = cura;
        #range0 = np.linspace(mina[0],maxa[0],10);
        range1 = np.linspace(mina[1],maxa[1],100);#100);
        #range2 = np.linspace(mina[2],maxa[2],20);
        range3 = np.linspace(mina[3],maxa[3],100);#10);
        #for p0 in range0:
        for p1 in range1:
            #for p2 in range2:
            for p3 in range3:
                cura = [0,p1,0,p3];
                # Check distance for this parameter combination
                d = np.sum((func(x,cura)-y)**2);
                if d<dmin:
                    dmin = d;
                    aForMinD = cura;
        #print('dmin for fit: ',dmin);
        return aForMinD,func(x,aForMinD);
        
    """
        Finds a fit for y = a[3]*(x**a[1]), returns the a array as well as the fit y.
        TODO: make this work for cases where dyin is 0 for some elements.
    """
    def findMSDFitError(self,xin,yin,dyin):
        pixelSize = self.pixelSize;
        x = np.array(xin);
        y = np.array(yin);
        dy = np.array(dyin);
        
        #func = lambda x,a: a[3]*((a[0]+x)**a[1])+a[2];
        func = lambda x,a: a[3]*(x**a[1]);    
        
        mina = [0,0,np.min(y),(pixelSize**2)*0];
        maxa = [np.min(x),3,np.max(y),(pixelSize**2)*0.01];
        
        # Loop parameters
        cura = mina;  
        dmin = np.sum((func(x,cura)-y)**2);
        aForMinD = cura;
        #range0 = np.linspace(mina[0],maxa[0],10);
        range1 = np.linspace(mina[1],maxa[1],100);
        #range2 = np.linspace(mina[2],maxa[2],20);
        range3 = np.linspace(mina[3],maxa[3],10);
        #for p0 in range0:
        for p1 in range1:
            #for p2 in range2:
            for p3 in range3:
                cura = [0,p1,0,p3];
                # Check distance for this parameter combination
                d = np.sum((func(x,cura)-y)**2/dy);
                if d<dmin:
                    dmin = d;
                    aForMinD = cura;
        return aForMinD,func(x,aForMinD);
        
    def analyzeMSD(self,x,y,index,saveGraph=True,saveCSV=False):
        plt = self.plt;
        
        # Looking at one file
        MDS_list, MDSerror_list, dt_list = self.getMSD(x,y);
        
        #print('np.mean(MDS_list)=',np.mean(MDS_list));
        
        # save to file
        if saveCSV:
            self.saveMSDToCVS(self.filename+"["+str(index)+"]-MSD.csv",range(1,len(MDS_list)),MDS_list,MDSerror_list);
        
        #print('np.array(MDS_list)/1e6[0] = ',np.array(MDS_list)[0]/1e6);
        
        # Fit
        x = np.array(dt_list);
        y = np.array(MDS_list);
        a,yfit = self.findMSDFit(x,y);
    
        if saveGraph:
            # Prepare plotting
            fig = plt.figure();
        
            plt.plot(dt_list,np.array(MDS_list)/1e6);
            plt.plot(dt_list,np.array(MDSerror_list)/1e6,'g');  
            plt.plot(x,np.array(yfit)/1e6,'r',linestyle='dashed');
            plt.xlabel('dt [frame]');
            plt.ylabel('Mean Distance Squared [$(\mu m)^2$]');
            plt.title('Mean Distance Squared Pre and Post Laser as a Function of Time');
        
            # Equation in plot
            mid1x = np.mean(x)*0.5;
            mid1y = np.mean(y)*1.8/1e6;
            plt.text(mid1x, mid1y, r'$y \propto '+str(round(a[0]/1e6,4))+'t^{'+str(round(a[1],3))+'}$', fontsize=15)
            #plt.show();
            fig.savefig(self.filename+"-MSD.jpeg");
            plt.close(fig);
        
    def getRollingAlpha(self,dt,saveToCSV=False,x=None,y=None):
        #x,y = self.x, self.y;
        if x is None:
            x = self.x;
        if y is None:
            y = self.y;
        #plt = self.plt; 
        
        # Prepare plotting
        #fig = plt.figure();
        #ax = fig.add_subplot(111);
        
        alphaList = [];
        qList = [];
        tList = [];
        add = int(dt/2);
        for i in range(add,len(x)-add,1):
            MDS_list, MSDerror_list, dt_list = self.getMSD(x[i-add:i+add],y[i-add:i+add]);
            a,yfit = self.findMSDFit(dt_list,MDS_list);
            alphaList.append(a[1]);
            qList.append(a[0]);
            tList.append(i);
            
        #print('std(q)/mean(q) is ',np.std(qList)/np.mean(qList)*100,'%');
        
        ##
        ## Sometimes dt is larger than len(x) so we get
        ## alphaList = []
        ##################################################
        if alphaList != [] and saveToCSV:
            self.saveRollingAlphaToCVS(alphaList,tList,dt);
        
        return tList, alphaList;
        
        