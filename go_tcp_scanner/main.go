package main

import (
	"fmt"
	"net"
	"sort"
	"time"
)

func worker(ports chan int, results chan int) {
	for port := range ports {
		address := fmt.Sprintf("scanme.nmap.org:%d", port)
		connection, err := net.Dial("tcp", address)

		if err != nil {
			results <- 0
			continue
		}
		results <- port
		connection.Close()
	}
}

func main() {

	ports := make(chan int, 100)
	results := make(chan int)
	var openPorts []int

	for i := 1; i <= cap(ports); i++ {
		go worker(ports, results)
	}

	go func() {
		for i := 1; i <= 10000; i++ {
			ports <- i
		}
	}()

	for i := 1; i <= 10000; i++ {
		port := <-results

		if port != 0 {
			fmt.Printf("Open port: %d\n", port)
			openPorts = append(openPorts, port)
		}
	}

	sort.Ints(openPorts)

	fmt.Println("Scan finished...")
	for _, port := range openPorts {
		fmt.Printf("Open port: %d\n", port)
	}
	close(ports)
	close(results)
}
