CC=g++
CFLAGS=-O3 -std=c++11 -Wall -I. -I./FromNIST
CFLAGS += -O3 -mavx2 -march=native


OBJS=conversions.o decode.o hash_wrapper.o kem.o ntl.o ring_buffer.o sampling.o \
     shake_prng.o threshold.o utilities.o FromNIST/rng.o

all: test_bike

test_bike: test_bike.o $(OBJS)
	$(CC) $(CFLAGS) -o test_bike test_bike.o $(OBJS) -lcrypto -lntl -lm

%.o: %.c
	gcc -O3 -std=c11 -Wall -I. -I./FromNIST -c $< -o $@

%.o: %.cpp
	$(CC) $(CFLAGS) -c $< -o $@

FromNIST/rng.o: FromNIST/rng.c
	gcc -O3 -std=c11 -Wall -I. -I./FromNIST -c FromNIST/rng.c -o FromNIST/rng.o

clean:
	rm -f *.o FromNIST/*.o test_bike bike_rendimiento.csv
