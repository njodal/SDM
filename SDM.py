import numpy as np
import unit_test as ut


class SDM(object):
    """
    Main class with the basic functionalities for any kind of SDM
    see: https://en.wikipedia.org/wiki/Sparse_distributed_memory
    """

    def __init__(self, address_length, content_length, number_of_hard_locations, radius, values_per_dimension=2,
                 debug=False):
        self.address_length           = address_length
        self.content_length           = content_length
        self.values_per_dimensions    = values_per_dimension
        self.max_possible_values      = self.values_per_dimensions ** self.content_length
        self.number_of_hard_locations = number_of_hard_locations
        self.radius                   = radius

        self.hard_locations = self.create_uniform_hard_locations(debug=debug)

    def write(self, address, content):
        for hard_location in self.get_hard_locations_in_distance(address, self.radius):
            for i, bit in enumerate(content):
                inc = 1 if bit == '1' else -1
                hard_location[1][i] += inc

    def read(self, content):
        return content

    def create_uniform_hard_locations(self, debug=False):
        distance = int(self.max_possible_values / self.number_of_hard_locations)
        if debug:
            print('create %s hard locations (d:%s)' % (self.number_of_hard_locations, distance))
        j = distance
        hard_locations = []
        for _ in range(self.number_of_hard_locations):
            address  = self.create_address(j)
            counters = self.create_counter()
            hard_locations.append((address, counters))
            if debug:
                print('   j:%s address:%s' % (j, address))
            j += distance
        return hard_locations

    def create_address(self, i):
        return np.binary_repr(i, width=self.content_length)

    def create_counter(self):
        return np.zeros(self.content_length, dtype=int)

    def get_hard_locations_in_distance(self, address, distance):
        """
        Returns the list of hard location that are near address
        :param address:
        :param distance: distance to be considered near
        :return:
        """
        hard_in_distance = [hard_location for hard_location in self.hard_locations
                            if self.address_distance(address, hard_location[0]) <= distance]
        return hard_in_distance

    def address_distance(self, address1, address2):
        return hamming_distance(address1, address2)


class BinarySDM(SDM):
    """
    Content is a binary message
    """

    def address_distance(self, address1, address2):
        return hamming_distance(address1, address2)

    def __init__(self, content_length, number_of_hard_locations, radius):
        super().__init__(content_length, number_of_hard_locations, radius, values_per_dimension=2)


def hamming_distance(binary1, binary2):
    """
    Returns the Hamming distance between to binary numbers
    :param binary1:
    :param binary2:
    :return:
    """
    d = 0
    for i in range(len(binary1)):
        if binary1[i] == binary2[i]:
            continue
        d += 1
    return d


# Tests
def test_create_hard_locations(address_length,content_length, number_of_hard_locations, radius, values_per_dimension,
                               debug):
    sdm = SDM(address_length, content_length, number_of_hard_locations, radius,
              values_per_dimension=values_per_dimension, debug=debug)
    return len(sdm.hard_locations)


def test_near_hard_locations(address, radius, hard_locations):
    near = [hard_location for hard_location in hard_locations if hamming_distance(address, hard_location) <= radius]
    return near


if __name__ == "__main__":
    ut.UnitTest(__name__, 'tests/SDM.test', '')
